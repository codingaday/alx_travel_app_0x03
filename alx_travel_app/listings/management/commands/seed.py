from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from alx_travel_app.listings.models import Listing
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with sample listings data'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding data...')
        self.create_hosts()
        self.create_listings()
        self.stdout.write(self.style.SUCCESS(
            '✅ Successfully seeded listings!'))

    def create_hosts(self):
        self.hosts = []

        sample_hosts = [
            {'email': 'host1@example.com', 'first_name': 'Alice', 'last_name': 'Host'},
            {'email': 'host2@example.com', 'first_name': 'Bob', 'last_name': 'Host'},
        ]

        for host in sample_hosts:
            user, created = User.objects.get_or_create(
                email=host['email'],
                defaults={
                    'first_name': host['first_name'],
                    'last_name': host['last_name'],
                    'role': 'host',
                    'password': 'password123'  # You can update this as needed
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            self.hosts.append(user)

    def create_listings(self):
        if Listing.objects.exists():
            self.stdout.write('Listings already exist. Skipping...')
            return

        names = [
            "Cozy Loft Downtown",
            "Modern Beachside Retreat",
            "Mountain Cabin Escape",
            "Stylish Studio Apartment",
            "Spacious Family Home"
        ]

        descriptions = [
            "A comfortable loft in the heart of the city.",
            "A peaceful getaway with beach views.",
            "Surround yourself with nature and quiet.",
            "Perfect spot for solo travelers or couples.",
            "Plenty of room for large families and groups."
        ]

        locations = [
            "New York, NY",
            "Santa Monica, CA",
            "Aspen, CO",
            "Austin, TX",
            "Orlando, FL"
        ]

        for i in range(5):
            Listing.objects.create(
                host=self.hosts[i % len(self.hosts)],
                name=names[i],
                description=descriptions[i],
                location=locations[i],
                pricepernight=random.randint(80, 350)
            )
