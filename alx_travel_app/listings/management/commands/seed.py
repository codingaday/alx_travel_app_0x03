
import random
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from listings.models import Booking, Listing, Review

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with sample listings, bookings, and reviews"

    def handle(self, *args, **options):
        self.stdout.write("Deleting existing data...")
        Listing.objects.all().delete()
        Booking.objects.all().delete()
        Review.objects.all().delete()

        self.stdout.write("Creating sample listings...")
        listings = []
        for i in range(1, 11):
            listing = Listing.objects.create(
                title=f"Beautiful Apartment #{i}",
                description=f"Spacious apartment with amazing views #{i}",
                price_per_night=round(random.uniform(50, 300), 2),
                max_guests=random.randint(1, 8),
            )
            listings.append(listing)
            self.stdout.write(f"Created listing: {listing.title}")

        # Create a test user
        user, created = User.objects.get_or_create(
            email="test@example.com",
            defaults={"username": "testuser", "password": "testpassword123"},
        )

        self.stdout.write("Creating sample bookings...")
        for listing in listings:
            start_date = datetime.now() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=random.randint(1, 14))

            Booking.objects.create(
                listing=listing,
                user=user,
                start_date=start_date,
                end_date=end_date,
                status=random.choice(["pending", "confirmed", "cancelled"]),
            )

        self.stdout.write("Creating sample reviews...")
        for listing in listings:
            Review.objects.create(
                listing=listing,
                user=user,
                rating=random.randint(1, 5),
                comment=f"Great experience at {listing.title}!",
            )

        self.stdout.write(
            self.style.SUCCESS("Database seeding completed successfully!")
        )
