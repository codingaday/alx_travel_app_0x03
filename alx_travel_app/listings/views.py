from rest_framework import viewsets
from .serializers import ListingSerializer, BookingSerializer
from .models import Listing, Booking
import uuid
import requests
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Payment
from .tasks import send_booking_confirmation_email
import os

# Create your views here.
CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY")
CHAPA_URL = "https://api.chapa.co/v1/transaction/initialize"


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    queryset = Listing.objects.all()

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        new_booking = serializer.save(user=self.request.user)
        send_booking_confirmation_email.delay(new_booking.id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    user = request.user
    amount = request.data.get("amount")
    booking_reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=user,
        booking_reference=booking_reference,
        amount=amount,
        status="Pending",
    )

    # Chapa request data
    data = {
        "amount": amount,
        "currency": "ETB",
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "tx_ref": booking_reference,
        "callback_url": f"http://localhost:8000/api/payments/verify/{booking_reference}/",
        "return_url": "http://localhost:8000/payment-success/",
        "customization[title]": "Booking Payment",
        "customization[description]": "Payment for travel booking",
    }

    headers = {
        "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{settings.CHAPA_BASE_URL.rstrip('/')}/transaction/initialize",
        json=data,  # ✅ use `json` instead of `data` so Chapa receives proper JSON
        headers=headers,
    )

    resp_json = response.json()

    if resp_json.get("status") == "success":
        payment.transaction_id = booking_reference
        payment.save()
        return Response({"payment_url": resp_json["data"]["checkout_url"]})
    else:
        return Response(resp_json, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_payment(request, booking_reference):
    try:
        payment = Payment.objects.get(booking_reference=booking_reference)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=404)

    headers = {
        "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
    }

    verify_url = (
        f"{settings.CHAPA_BASE_URL.rstrip('/')}/transaction/verify/{booking_reference}"
    )

    response = requests.get(verify_url, headers=headers)
    resp_json = response.json()

    if (
        resp_json.get("status") == "success"
        and resp_json["data"]["status"] == "success"
    ):
        payment.status = "Completed"
        payment.save()

        # Send confirmation email
        send_mail(
            "Payment Confirmation",
            "Your booking payment was successful.",
            "noreply@mytravel.com",
            [payment.user.email],
        )

        return Response({"message": "Payment verified successfully"})
    else:
        payment.status = "Failed"
        payment.save()
        return Response({"message": "Payment verification failed"}, status=400)
