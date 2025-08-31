
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Listing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "price_per_night",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("max_guests", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("confirmed", "Confirmed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "listing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bookings",
                        to="listings.listing",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "rating",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "1 Star"),
                            (2, "2 Stars"),
                            (3, "3 Stars"),
                            (4, "4 Stars"),
                            (5, "5 Stars"),
                        ]
                    ),
                ),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "listing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="listings.listing",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="ETB", max_length=3)),
                (
                    "payment_method",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("telebirr", "Telebirr"),
                            ("cbe", "CBE Birr"),
                            ("ebirr", "Ebirr"),
                            ("mpesa", "Mpesa"),
                            ("bank", "Bank Transfer"),
                        ],
                        max_length=20,
                    ),
                ),
                ("transaction_id", models.CharField(max_length=100, unique=True)),
                ("checkout_url", models.URLField(blank=True, null=True)),
                ("booking_reference", models.CharField(max_length=100, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("customer_email", models.EmailField(max_length=254)),
                ("customer_name", models.CharField(max_length=255)),
                ("customer_phone", models.CharField(blank=True, max_length=15)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("chapa_response_data", models.JSONField(blank=True, default=dict)),
                (
                    "booking",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment",
                        to="listings.booking",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["transaction_id"], name="listings_pa_transac_0240af_idx"
                    ),
                    models.Index(
                        fields=["status"], name="listings_pa_status_98563c_idx"
                    ),
                    models.Index(
                        fields=["created_at"], name="listings_pa_created_5fdebf_idx"
                    ),
                ],
            },
        ),
    ]
