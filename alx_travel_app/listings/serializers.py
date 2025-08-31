
import re

from django.utils import timezone
from rest_framework import serializers

from .models import Booking, Listing, Payment, Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.
    """

    class Meta:
        model = Review
        fields = ["id", "user", "listing", "rating", "comment", "created_at"]
        read_only_fields = (
            "id",
            "user",
            "created_at",
        )
        extra_kwargs = {"user": {"read_only": True}, "listing": {"read_only": True}}

    def validate_rating(self, value):
        """Check that the rating is between 1 and 5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        """Create a new review with the authenticated user."""
        # Set the user from the request context
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Listing model.
    """

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "price_per_night",
            "max_guests",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_price_per_night(self, value):
        """Ensure price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_max_guests(self, value):
        """Ensure max_guests is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Maximum guests must be greater than zero."
            )
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model.
    """

    booking_details = serializers.SerializerMethodField()
    is_successful = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "booking_details",
            "amount",
            "currency",
            "payment_method",
            "transaction_id",
            "checkout_url",
            "booking_reference",
            "status",
            "customer_email",
            "customer_name",
            "customer_phone",
            "created_at",
            "updated_at",
            "completed_at",
            "is_successful",
            "is_pending",
        ]
        read_only_fields = [
            "id",
            "transaction_id",
            "checkout_url",
            "booking_reference",
            "status",
            "created_at",
            "updated_at",
            "completed_at",
            "is_successful",
            "is_pending",
        ]

    def get_booking_details(self, obj):
        """Get basic booking information for the payment."""
        if obj.booking:
            return {
                "id": obj.booking.id,
                "listing_title": obj.booking.listing.title,
                "start_date": obj.booking.start_date,
                "end_date": obj.booking.end_date,
                "total_nights": (obj.booking.end_date - obj.booking.start_date).days,
            }
        return None


class PaymentInitiationSerializer(serializers.Serializer):
    """
    Serializer for payment initiation request.
    """

    booking_id = serializers.IntegerField()
    customer_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Phone number in format: +251912345678 or 0912345678",
    )
    return_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="URL to redirect user after payment completion",
    )

    def validate_booking_id(self, value):
        """Validate that booking exists and can be paid for."""
        try:
            booking = Booking.objects.select_related("listing", "user").get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        # Check if booking already has a successful payment
        if hasattr(booking, "payment") and booking.payment.is_successful:
            raise serializers.ValidationError("This booking has already been paid for.")

        # Check if booking belongs to the current user
        request = self.context.get("request")
        if request and booking.user != request.user:
            raise serializers.ValidationError("You can only pay for your own bookings.")

        # Check if booking is not cancelled
        if booking.status == "cancelled":
            raise serializers.ValidationError("Cannot pay for a cancelled booking.")

        # Check if booking dates are valid (not in the past)
        if booking.start_date < timezone.now().date():
            raise serializers.ValidationError(
                "Cannot pay for bookings with past dates."
            )

        return value

    def validate_customer_phone(self, value):
        """Validate phone number format."""
        if not value:
            return value

        # Remove all non-digit characters for validation
        digits_only = re.sub(r"\D", "", value)

        # Check if it's a reasonable length
        if len(digits_only) < 9 or len(digits_only) > 15:
            raise serializers.ValidationError(
                "Phone number must be between 9 and 15 digits long."
            )

        # For Ethiopian numbers, provide specific validation
        if digits_only.startswith("251"):
            # Country code + 9 digits
            if len(digits_only) != 12:
                raise serializers.ValidationError(
                    "Ethiopian phone number with country code must be 12 digits (251xxxxxxxxx)."
                )
        elif digits_only.startswith("0"):
            # Local format starting with 0
            if len(digits_only) != 10:
                raise serializers.ValidationError(
                    "Ethiopian phone number starting with 0 must be 10 digits (09xxxxxxxx)."
                )
        elif len(digits_only) == 9:
            # Local format without leading 0
            if not digits_only.startswith("9"):
                raise serializers.ValidationError(
                    "Ethiopian phone number must start with 9 when using 9-digit format."
                )

        return value

    def validate_return_url(self, value):
        """Validate return URL format."""
        if not value:
            return value

        # Check if URL is valid and uses https in production
        if value.startswith("http://localhost") or value.startswith("http://127.0.0.1"):
            # Allow localhost for development
            return value
        elif not value.startswith("https://"):
            raise serializers.ValidationError(
                "Return URL must use HTTPS protocol for security."
            )

        return value

    def validate(self, data):
        """Cross-field validation."""
        request = self.context.get("request")

        if request:
            # Validate user has required information for payment
            user = request.user
            if not user.email or "@" not in user.email:
                raise serializers.ValidationError(
                    "A valid email address is required for payment processing. "
                    "Please update your profile."
                )

        return data


class PaymentVerificationSerializer(serializers.Serializer):
    """
    Serializer for payment verification request.
    """

    tx_ref = serializers.CharField(
        max_length=100, help_text="Transaction reference to verify"
    )

    def validate_tx_ref(self, value):
        """Validate that payment with this reference exists."""
        try:
            payment = Payment.objects.select_related("booking", "booking__user").get(
                booking_reference=value
            )
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")

        # Check if user can access this payment
        request = self.context.get("request")
        if request and not request.user.is_staff:
            if payment.booking.user != request.user:
                raise serializers.ValidationError("Access denied.")

        return value


class PaymentStatusSerializer(serializers.Serializer):
    """
    Serializer for payment status responses.
    """

    success = serializers.BooleanField()
    status = serializers.CharField()
    payment_id = serializers.UUIDField()
    booking_status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    verified_at = serializers.DateTimeField()
    checkout_url = serializers.URLField(required=False)
    reference = serializers.CharField()
    error = serializers.CharField(required=False)
    details = serializers.DictField(required=False)


class PaymentWebhookSerializer(serializers.Serializer):
    """
    Serializer for Chapa webhook data validation.
    """

    tx_ref = serializers.CharField(required=True)
    status = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)

    def validate_status(self, value):
        """Validate webhook status values."""
        valid_statuses = ["success", "failed", "cancelled", "pending"]
        if value.lower() not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value.lower()


# Enhanced booking serializer with payment information
class BookingWithPaymentSerializer(serializers.ModelSerializer):
    """
    Enhanced booking serializer that includes payment information.
    """

    payment = PaymentSerializer(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    can_pay = serializers.SerializerMethodField()
    nights_count = serializers.SerializerMethodField()
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    listing_price = serializers.DecimalField(
        source="listing.price_per_night",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "listing",
            "listing_title",
            "listing_price",
            "user",
            "start_date",
            "end_date",
            "nights_count",
            "status",
            "total_amount",
            "created_at",
            "payment",
            "can_pay",
        ]
        read_only_fields = (
            "id",
            "created_at",
            "total_amount",
            "payment",
            "can_pay",
            "nights_count",
        )
        extra_kwargs = {"user": {"read_only": True}, "status": {"required": False}}

    def get_can_pay(self, obj):
        """Determine if this booking can be paid for."""
        if obj.status == "cancelled":
            return False

        if hasattr(obj, "payment") and obj.payment.is_successful:
            return False

        if obj.start_date < timezone.now().date():
            return False

        return True

    def get_nights_count(self, obj):
        """Calculate number of nights for the booking."""
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days
        return 0

    def validate(self, data):
        """
        Validate booking dates and availability.
        """
        # Check if start_date is before end_date
        if data["start_date"] >= data["end_date"]:
            raise serializers.ValidationError("End date must be after start date.")

        # Check if booking is for at least 1 night
        if (data["end_date"] - data["start_date"]).days < 1:
            raise serializers.ValidationError("Booking must be for at least one night.")

        # Check if booking is not in the past
        if data["start_date"] < timezone.now().date():
            raise serializers.ValidationError("Cannot book for past dates.")

        # Check if listing exists and is available
        listing = data.get("listing")
        if listing:
            # Check for overlapping bookings
            overlapping_bookings = Booking.objects.filter(
                listing=listing,
                start_date__lt=data["end_date"],
                end_date__gt=data["start_date"],
                status__in=["pending", "confirmed"],
            )

            # Exclude current instance when updating
            if self.instance:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.instance.pk)

            if overlapping_bookings.exists():
                raise serializers.ValidationError(
                    "This listing is already booked for the selected dates."
                )

        return data
