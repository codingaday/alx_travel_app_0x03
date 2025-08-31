
import logging
from typing import Any

from .models import Booking
from .serializers import BookingSerializer
from .tasks import send_booking_confirmation_email


from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .chapa_service import ChapaService
from .models import Booking, Listing, Payment, Review
from .serializers import (
    BookingWithPaymentSerializer,
    ListingSerializer,
    PaymentInitiationSerializer,
    PaymentSerializer,
    PaymentVerificationSerializer,
    ReviewSerializer,
)
from .tasks import send_payment_confirmation_email, send_payment_failure_email

logger = logging.getLogger(__name__)


class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows listings to be viewed or edited.
    """

    queryset = Listing.objects.all().order_by("-created_at")
    serializer_class = ListingSerializer
    lookup_field = "id"

    def get_queryset(self):
        """
        Optionally filter listings by various parameters.
        """
        queryset = super().get_queryset()
        # Example of filtering by query parameters
        max_price = self.request.query_params.get("max_price")
        if max_price is not None:
            queryset = queryset.filter(price_per_night__lte=max_price)
        return queryset

    @action(detail=True, methods=["get"])
    def reviews(self, request, id=None):
        """
        Retrieve all reviews for a specific listing.
        """
        listing = self.get_object()
        reviews = Review.objects.filter(listing=listing)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows bookings to be viewed or edited.
    """

    serializer_class = BookingWithPaymentSerializer
    lookup_field = "id"

    def get_queryset(self) -> Any:
        """
        Optionally filter bookings by listing_id or user.
        """
        queryset = Booking.objects.all().order_by("-created_at")
        listing_id = self.request.GET.get("listing_id")
        user_id = self.request.GET.get("user_id")

        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def perform_create(self, serializer):
        """
        Automatically set the user to the current user when creating a booking.
        """
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to prevent deletion of confirmed bookings.
        """
        instance = self.get_object()
        if instance.status == "confirmed":
            return Response(
                {"detail": "Cannot delete a confirmed booking."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Handle PATCH requests for updating a booking.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Save the updated instance
        self.perform_update(serializer)

        # Refresh the instance from the database to get the updated status
        instance.refresh_from_db()

        return Response(serializer.data)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing payments.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self) -> Any:
        """
        Filter payments to show only user's own payments unless admin.
        """
        queryset = Payment.objects.all().order_by("-created_at")

        # Non-admin users can only see their own payments
        if not self.request.user.is_staff:
            queryset = queryset.filter(booking__user=self.request.user)

        return queryset

    def _get_user_details(self, user):
        """
        Extract and validate user details for payment processing.
        
        Args:
            user: Django User instance
            
        Returns:
            dict: Dictionary containing cleaned user details
        """
        # Get user details with fallbacks
        first_name = user.first_name.strip() if user.first_name else ""
        last_name = user.last_name.strip() if user.last_name else ""
        
        # If names are empty, try to extract from username or email
        if not first_name and not last_name:
            if hasattr(user, 'username') and user.username:
                username = user.username.strip()
                if '@' in username:
                    # Username is an email
                    email_user = username.split('@')[0]
                    if '_' in email_user or '.' in email_user:
                        parts = email_user.replace('_', '.').split('.')
                        if len(parts) >= 2:
                            first_name = parts[0].capitalize()
                            last_name = parts[1].capitalize()
                        else:
                            first_name = parts[0].capitalize()
                            last_name = "User"
                    else:
                        first_name = username.capitalize()
                        last_name = "User"
                else:
                    # Regular username
                    first_name = username.capitalize()
                    last_name = "User"
            else:
                # Extract from email as last resort
                email_user = user.email.split('@')[0]
                first_name = email_user.capitalize()
                last_name = "User"
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'email': user.email,
            'full_name': f"{first_name} {last_name}".strip()
        }

    @action(detail=False, methods=["post"])
    def initiate(self, request):
        """
        Initiate a new payment.
        """
        serializer = PaymentInitiationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        booking_id = serializer.validated_data["booking_id"]
        
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        except Exception as e:
            logger.error(f"Booking not found or access denied: {booking_id} for user {request.user.id}")
            return Response(
                {"error": "Booking not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def status(self, request):
        """
        Get payment status by transaction reference (GET method for easier frontend integration).
        This doesn't verify with Chapa, just returns current database status.
        """
        tx_ref = request.query_params.get('tx_ref')
        
        if not tx_ref:
            return Response(
                {"error": "tx_ref parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.select_related('booking', 'booking__user', 'booking__listing').get(
                booking_reference=tx_ref
            )

            # Check if user can access this payment
            if not request.user.is_staff and payment.booking.user != request.user:
                return Response(
                    {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
                )

            return Response(
                {
                    "success": True,
                    "status": payment.status,
                    "payment_id": str(payment.id),
                    "booking_id": payment.booking.id,
                    "booking_status": payment.booking.status,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "checkout_url": payment.checkout_url,
                    "created_at": payment.created_at,
                    "updated_at": payment.updated_at,
                    "completed_at": payment.completed_at,
                    "is_successful": payment.is_successful,
                    "is_pending": payment.is_pending,
                    "listing_title": payment.booking.listing.title,
                    "customer_name": payment.customer_name,
                    "customer_email": payment.customer_email,
                    "transaction_id": payment.transaction_id,
                }
            )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting payment status for {tx_ref}: {str(e)}")
            return Response(
                {"error": "Failed to retrieve payment status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Check if payment already exists and is successful
        if hasattr(booking, "payment") and booking.payment.is_successful:
            return Response(
                {"error": "This booking has already been paid for."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get user details
        user_details = self._get_user_details(request.user)
        
        # Validate that we have a valid email
        if not user_details['email'] or '@' not in user_details['email']:
            return Response(
                {
                    "error": "Valid email address is required for payment processing. "
                           "Please update your profile with a valid email address."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get additional data from request
        customer_phone = serializer.validated_data.get("customer_phone", "")
        return_url = serializer.validated_data.get(
            "return_url", "http://localhost:3000/payment-success"
        )
        callback_url = request.build_absolute_uri("/api/v1/payments/webhook/")

        logger.info(f"Processing payment initiation for booking {booking_id}")
        logger.info(f"User details: email={user_details['email']}, name={user_details['full_name']}")

        try:
            with transaction.atomic():
                # Create or update payment record
                payment, created = Payment.objects.get_or_create(
                    booking=booking,
                    defaults={
                        "amount": booking.total_amount,
                        "currency": "ETB",
                        "customer_email": user_details['email'],
                        "customer_name": user_details['full_name'],
                        "customer_phone": customer_phone,
                        "booking_reference": ChapaService().generate_reference(),
                        "status": "pending",
                    },
                )

                if not created:
                    # Update existing payment if needed
                    payment.customer_email = user_details['email']
                    payment.customer_name = user_details['full_name']
                    payment.customer_phone = customer_phone
                    payment.status = "pending"
                    payment.save()

                # Initialize Chapa service and initiate payment
                chapa_service = ChapaService()
                success, chapa_response = chapa_service.initiate_payment(
                    amount=booking.total_amount,
                    email=user_details['email'],
                    first_name=user_details['first_name'],
                    last_name=user_details['last_name'],
                    phone_number=customer_phone,
                    tx_ref=payment.booking_reference,
                    callback_url=callback_url,
                    return_url=return_url,
                    description=f"Booking for {booking.listing.title}",
                )

                if success:
                    chapa_data = chapa_response.get("data", {})
                    payment.transaction_id = chapa_data.get(
                        "tx_ref", payment.booking_reference
                    )
                    payment.checkout_url = chapa_data.get("checkout_url", "")
                    payment.status = "processing"
                    payment.chapa_response_data = chapa_response
                    payment.save()

                    logger.info(f"Payment initiated successfully: {payment.booking_reference}")

                    return Response(
                        {
                            "success": True,
                            "payment_id": str(payment.id),
                            "checkout_url": payment.checkout_url,
                            "reference": payment.booking_reference,
                            "amount": str(payment.amount),
                            "currency": payment.currency,
                        }
                    )
                else:
                    error_msg = chapa_response.get("error", "Payment initiation failed")
                    error_details = chapa_response.get("details", {})
                    
                    logger.error(f"Payment initiation failed: {error_msg}")
                    if error_details:
                        logger.error(f"Error details: {error_details}")
                    
                    # Provide more user-friendly error messages
                    if "email" in str(error_details).lower():
                        error_msg = "Invalid email address. Please check your email and try again."
                    elif "phone" in str(error_details).lower():
                        error_msg = "Invalid phone number format. Please check your phone number and try again."
                    elif "amount" in str(error_details).lower():
                        error_msg = "Invalid payment amount. Please try again."
                    
                    return Response(
                        {
                            "success": False,
                            "error": error_msg,
                            "details": error_details if request.user.is_staff else None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            logger.error(f"Error in payment initiation: {str(e)}")
            return Response(
                {"error": "Payment initiation failed. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def verify(self, request):
        """
        Verify payment status.
        """
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx_ref = serializer.validated_data["tx_ref"]

        try:
            payment = Payment.objects.get(booking_reference=tx_ref)

            # Check if user can access this payment
            if not request.user.is_staff and payment.booking.user != request.user:
                return Response(
                    {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
                )

            # Verify with Chapa
            chapa_service = ChapaService()
            success, chapa_response = chapa_service.verify_payment(tx_ref)

            if success:
                chapa_data = chapa_response.get("data", {})
                chapa_status = chapa_data.get("status", "").lower()

                # Update payment status
                old_status = payment.status
                if chapa_status == "success":
                    payment.status = "completed"
                    payment.completed_at = timezone.now()
                    payment.booking.status = "confirmed"
                    payment.booking.save()

                    # Send confirmation email if status changed
                    if old_status != "completed":
                        send_payment_confirmation_email.delay(
                            payment.booking.id, str(payment.id)
                        )

                elif chapa_status in ["failed", "cancelled"]:
                    payment.status = chapa_status

                    # Send failure email if status changed
                    if old_status not in ["failed", "cancelled"]:
                        send_payment_failure_email.delay(
                            payment.booking.pk,
                            str(payment.id),
                            chapa_data.get("message", ""),
                        )

                payment.chapa_response_data.update(chapa_response)
                payment.save()

                return Response(
                    {
                        "success": True,
                        "status": payment.status,
                        "payment_id": str(payment.id),
                        "booking_status": payment.booking.status,
                        "verified_at": timezone.now(),
                        "amount": str(payment.amount),
                        "currency": payment.currency,
                    }
                )
            else:
                error_msg = chapa_response.get("error", "Payment verification failed")
                return Response(
                    {
                        "success": False,
                        "error": error_msg,
                        "details": chapa_response if request.user.is_staff else None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], permission_classes=[])
    def webhook(self, request):
        """
        Webhook endpoint for Chapa payment notifications.
        """
        try:
            # Extract data from webhook
            webhook_data = request.data
            tx_ref = webhook_data.get("tx_ref")
            status = webhook_data.get("status", "").lower()

            if not tx_ref:
                logger.warning("Webhook received without tx_ref")
                return Response(
                    {"error": "Missing tx_ref"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Find the payment
            try:
                payment = Payment.objects.get(booking_reference=tx_ref)
            except Payment.DoesNotExist:
                logger.warning(f"Webhook received for unknown payment: {tx_ref}")
                return Response(
                    {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Update payment status based on webhook
            old_status = payment.status

            if status == "success":
                payment.status = "completed"
                payment.completed_at = timezone.now()
                payment.booking.status = "confirmed"
                payment.booking.save()

                # Send confirmation email
                if old_status != "completed":
                    send_payment_confirmation_email.delay(
                        payment.booking.id, str(payment.id)
                    )

            elif status in ["failed", "cancelled"]:
                payment.status = status

                # Send failure email
                if old_status not in ["failed", "cancelled"]:
                    send_payment_failure_email.delay(
                        payment.booking.pk,
                        str(payment.id),
                        webhook_data.get("message", ""),
                    )

            # Update response data
            payment.chapa_response_data.update(webhook_data)
            payment.save()

            logger.info(f"Webhook processed for payment {tx_ref}: {status}")

            return Response({"success": True, "message": "Webhook processed"})

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return Response(
                {"error": "Webhook processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        # Trigger async email
        if booking.customer_email:
            send_booking_confirmation_email.delay(booking.customer_email, booking.id)
