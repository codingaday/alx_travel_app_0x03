
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from listings.models import Booking, Listing

User = get_user_model()


class Command(BaseCommand):
    help = "Create sample data for testing payment integration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=3, help="Number of sample users to create"
        )
        parser.add_argument(
            "--listings",
            type=int,
            default=5,
            help="Number of sample listings to create",
        )

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data...")

        # Create sample users
        users_created = 0
        for i in range(options["users"]):
            username = f"user{i + 1}"
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"user{i + 1}@example.com",
                    first_name=f"User{i + 1}",
                    last_name="Test",
                    password="testpass123",
                )
                users_created += 1
                self.stdout.write(f"Created user: {user.username}")

        # Create admin user if not exists
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="Test",
                password="admin123",
            )
            self.stdout.write(f"Created admin user: {admin.username}")

        # Sample listing data
        sample_listings = [
            {
                "title": "Beachfront Villa in Bahir Dar",
                "description": "Stunning lakeside villa with panoramic views of Lake Tana. Perfect for families and groups looking for a peaceful retreat.",
                "price_per_night": Decimal("350.00"),
                "max_guests": 8,
            },
            {
                "title": "Historic Castle View in Gondar",
                "description": "Traditional Ethiopian house with views of the famous Gondar castles. Walking distance to major historical sites.",
                "price_per_night": Decimal("180.00"),
                "max_guests": 4,
            },
            {
                "title": "Mountain Lodge in Simien Mountains",
                "description": "Eco-friendly mountain lodge perfect for trekking adventures. Includes guided tours and traditional meals.",
                "price_per_night": Decimal("280.00"),
                "max_guests": 6,
            },
            {
                "title": "Urban Apartment in Addis Ababa",
                "description": "Modern apartment in the heart of Addis Ababa. Close to restaurants, shopping, and cultural attractions.",
                "price_per_night": Decimal("120.00"),
                "max_guests": 3,
            },
            {
                "title": "Desert Camp in Danakil Depression",
                "description": "Unique desert camping experience in one of the most extreme environments on Earth. Professional guides included.",
                "price_per_night": Decimal("450.00"),
                "max_guests": 4,
            },
            {
                "title": "Coffee Farm Stay in Yirgacheffe",
                "description": "Experience authentic Ethiopian coffee culture on a working coffee farm. Includes coffee ceremonies and farm tours.",
                "price_per_night": Decimal("200.00"),
                "max_guests": 5,
            },
            {
                "title": "Rock Church Retreat in Lalibela",
                "description": "Spiritual retreat near the famous rock-hewn churches of Lalibela. Includes guided spiritual tours.",
                "price_per_night": Decimal("320.00"),
                "max_guests": 4,
            },
        ]

        # Create sample listings
        listings_created = 0
        for i, listing_data in enumerate(sample_listings[: options["listings"]]):
            if not Listing.objects.filter(title=listing_data["title"]).exists():
                listing = Listing.objects.create(**listing_data)
                listings_created += 1
                self.stdout.write(f"Created listing: {listing.title}")

        # Create some sample bookings for testing
        users = User.objects.filter(is_superuser=False)[:2]
        listings = Listing.objects.all()[:3]

        if users and listings:
            bookings_created = 0
            for user in users:
                for i, listing in enumerate(listings):
                    start_date = date.today() + timedelta(days=(i * 7) + 1)
                    end_date = start_date + timedelta(days=3)

                    if not Booking.objects.filter(
                        user=user, listing=listing, start_date=start_date
                    ).exists():
                        booking = Booking.objects.create(
                            user=user,
                            listing=listing,
                            start_date=start_date,
                            end_date=end_date,
                            status="pending",
                        )
                        bookings_created += 1
                        self.stdout.write(
                            f"Created booking: {user.username} -> {listing.title}"
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSample data creation complete!\n"
                f"Users created: {users_created}\n"
                f"Listings created: {listings_created}\n"
                f"Bookings created: {bookings_created}\n"
            )
        )
