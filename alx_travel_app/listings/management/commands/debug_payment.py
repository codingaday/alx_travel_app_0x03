
import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from listings.chapa_service import ChapaService
from listings.models import Booking

User = get_user_model()


class Command(BaseCommand):
    help = "Debug payment issues and test Chapa integration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            help="User ID to debug",
        )
        parser.add_argument(
            "--booking-id",
            type=int,
            help="Booking ID to test payment for",
        )
        parser.add_argument(
            "--test-user-data",
            action="store_true",
            help="Test user data validation",
        )
        parser.add_argument(
            "--test-chapa-connection",
            action="store_true",
            help="Test Chapa API connection",
        )

    def handle(self, *args, **options):
        if options["test_chapa_connection"]:
            self.test_chapa_connection()

        if options["test_user_data"]:
            self.test_user_data(options.get("user_id"))

        if options["booking_id"]:
            self.test_booking_payment(options["booking_id"])

    def test_chapa_connection(self):
        """Test Chapa API connection and configuration."""
        self.stdout.write(self.style.HTTP_INFO("Testing Chapa API configuration..."))

        chapa_service = ChapaService()

        # Check configuration
        self.stdout.write(f"Base URL: {chapa_service.base_url}")
        self.stdout.write(
            f"Secret Key configured: {'Yes' if chapa_service.secret_key else 'No'}"
        )
        self.stdout.write(
            f"Secret Key length: {len(chapa_service.secret_key) if chapa_service.secret_key else 0}"
        )

        # Test with different email formats to see what Chapa accepts
        test_emails = [
            "abebe.kebede@gmail.com",  # Ethiopian-style name
            "meron.tesfaye@yahoo.com",  # Another Ethiopian name
            "dawit_solomon@gmail.com",  # Underscore format
            "customer.test@hotmail.com",  # Standard format
            "user123@outlook.com",  # Simple format
        ]

        self.stdout.write(self.style.HTTP_INFO("\nTesting different email formats..."))

        for test_email in test_emails:
            self.stdout.write(f"\nTesting email: {test_email}")

            success, response = chapa_service.initiate_payment(
                amount=100,
                email=test_email,
                first_name="Test",
                last_name="User",
                phone_number="+251912345678",
                description="Test payment",
            )

            if success:
                self.stdout.write(self.style.SUCCESS(f"Email {test_email} accepted"))
                # Just test one successful email
                break
            else:
                error_details = response.get("error", {})
                if "email" in str(error_details).lower():
                    self.stdout.write(
                        self.style.ERROR(
                            f"Email {test_email} rejected: {error_details}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"? Email {test_email} - other error: {error_details}"
                        )
                    )

        # Final test result
        if success:
            self.stdout.write(self.style.SUCCESS("\nChapa API connection successful"))
        else:
            self.stdout.write(self.style.ERROR("\nChapa API connection failed"))
            self.stdout.write(f"Latest error: {json.dumps(response, indent=2)}")

        # Test the current user's email if we have one
        self.stdout.write(self.style.HTTP_INFO("\nTesting actual user emails..."))
        try:
            user = User.objects.first()
            if user and user.email:
                success, response = chapa_service.initiate_payment(
                    amount=100,
                    email=user.email,
                    first_name=user.first_name or "Test",
                    last_name=user.last_name or "User",
                    phone_number="+251912345678",
                    description="Test payment",
                )

                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"Real user email works: {user.email}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Real user email failed: {user.email}")
                    )
                    self.stdout.write(f"Error: {json.dumps(response, indent=2)}")
            else:
                self.stdout.write("No users found to test with")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error testing user email: {e}"))

    def test_user_data(self, user_id=None):
        """Test user data validation."""
        self.stdout.write(self.style.HTTP_INFO("Testing user data validation..."))

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                users = [user]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
                return
        else:
            users = User.objects.all()[:5]  # Test first 5 users

        chapa_service = ChapaService()

        for user in users:
            self.stdout.write(f"\nTesting user: {user.pk} - {user.username}")

            # Test email validation
            try:
                validated_email = chapa_service._validate_email(user.email)
                self.stdout.write(f"  ✓ Email: {validated_email}")
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Email error: {e}"))

            # Test name validation
            try:
                first_name = chapa_service._clean_name(user.first_name, "first_name")
                last_name = chapa_service._clean_name(user.last_name, "last_name")
                self.stdout.write(f"  ✓ Names: '{first_name}' '{last_name}'")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Name error: {e}"))

            # Show original vs cleaned data
            self.stdout.write(
                f"  Original: first='{user.first_name}', last='{user.last_name}', email='{user.email}'"
            )

            # Test phone validation if available
            if hasattr(user, "phone") and user.phone:
                try:
                    cleaned_phone = chapa_service._clean_phone(user.phone)
                    self.stdout.write(f"  Phone: {cleaned_phone}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Phone error: {e}"))

    def test_booking_payment(self, booking_id):
        """Test payment initiation for a specific booking."""
        self.stdout.write(
            self.style.HTTP_INFO(f"Testing payment for booking {booking_id}...")
        )

        try:
            booking = Booking.objects.select_related("user", "listing").get(
                id=booking_id
            )
        except Booking.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Booking with ID {booking_id} not found")
            )
            return

        self.stdout.write(f"Booking: {booking}")
        self.stdout.write(f"User: {booking.user.username} ({booking.user.email})")
        self.stdout.write(f"Amount: {booking.total_amount} ETB")

        # Test payment initiation
        chapa_service = ChapaService()

        # Clean user data
        try:
            validated_email = chapa_service._validate_email(booking.user.email)
            first_name = chapa_service._clean_name(booking.user.first_name)
            last_name = chapa_service._clean_name(booking.user.last_name)

            self.stdout.write("Cleaned data: ")
            self.stdout.write(f"  Email: {validated_email}")
            self.stdout.write(f"  First name: {first_name}")
            self.stdout.write(f"  Last name: {last_name}")

            # Try payment initiation
            success, response = chapa_service.initiate_payment(
                amount=booking.total_amount,
                email=validated_email,
                first_name=first_name,
                last_name=last_name,
                description=f"Test payment for {booking.listing.title}",
            )

            if success:
                self.stdout.write(self.style.SUCCESS("Payment initiation successful"))
                data = response.get("data", {})
                self.stdout.write(f"Checkout URL: {data.get('checkout_url')}")
                self.stdout.write(f"TX Ref: {data.get('tx_ref')}")
            else:
                self.stdout.write(self.style.ERROR("Payment initiation failed"))
                self.stdout.write(f"Error: {json.dumps(response, indent=2)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Data validation error: {e}"))

    def style_json(self, data):
        """Pretty print JSON data."""
        return json.dumps(data, indent=2, default=str)
