
import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Listing(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="bookings"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.listing.title}"

    @property
    def total_amount(self):
        """Calculate the total amount for the booking."""
        if not self.start_date or not self.end_date or not self.listing:
            return 0
        num_nights = (self.end_date - self.start_date).days
        return self.listing.price_per_night * num_nights


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("telebirr", "Telebirr"),
        ("cbe", "CBE Birr"),
        ("ebirr", "Ebirr"),
        ("mpesa", "Mpesa"),
        ("bank", "Bank Transfer"),
    ]

    # Primary key as UUID for better security
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship with booking
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="payment"
    )

    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="ETB")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True
    )

    # Chapa transaction details
    transaction_id = models.CharField(max_length=100, unique=True)
    checkout_url = models.URLField(blank=True, null=True)
    booking_reference = models.CharField(max_length=100, unique=True)

    # Payment status and metadata
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )

    # User information for payment
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=15, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Additional metadata from Chapa
    chapa_response_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Payment {self.booking_reference} - {self.status}"

    @property
    def is_successful(self):
        return self.status == "completed"

    @property
    def is_pending(self):
        return self.status in ["pending", "processing"]


class Review(models.Model):
    RATING_CHOICES = [
        (1, "1 Star"),
        (2, "2 Stars"),
        (3, "3 Stars"),
        (4, "4 Stars"),
        (5, "5 Stars"),
    ]

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating} stars for {self.listing.title}"
