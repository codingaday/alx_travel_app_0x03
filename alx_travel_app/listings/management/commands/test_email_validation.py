
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from listings.chapa_service import ChapaService

User = get_user_model()


class Command(BaseCommand):
    help = "Test email validation for Chapa integration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("Testing email validation for Chapa..."))

        # Test different email formats
        test_cases = [
            # Format: (email, expected_to_work, description)
            ("admin@travelapp.com", False, "Your current email"),
            ("abebe.kebede@gmail.com", True, "Ethiopian name with Gmail"),
            ("meron_tesfaye@yahoo.com", True, "Ethiopian name with Yahoo"),
            ("test@gmail.com", True, "Simple Gmail"),
            ("user123@hotmail.com", True, "Hotmail with numbers"),
            ("customer@outlook.com", True, "Outlook"),
            ("demo@example.com", False, "Example.com domain (blocked)"),
            ("test..email@gmail.com", False, "Double dots (invalid)"),
            (".test@gmail.com", False, "Leading dot (invalid)"),
            ("test@.gmail.com", False, "Invalid domain"),
            (
                "very.long.email.address.that.might.be.too.long.for.chapa@verylongdomainname.com",
                False,
                "Very long email",
            ),
        ]

        chapa_service = ChapaService()

        for email, expected_to_work, description in test_cases:
            self.stdout.write(f"\nTesting: {email} ({description})")

            # First test our internal validation
            try:
                validated_email = chapa_service._validate_email(email)
                self.stdout.write(f"  ✓ Internal validation passed: {validated_email}")

                # If internal validation passes, test with Chapa
                success, response = chapa_service.initiate_payment(
                    amount=100,
                    email=validated_email,
                    first_name="Test",
                    last_name="User",
                    phone_number="0912345678",  # Use Ethiopian format
                    description="Email validation test",
                )

                if success:
                    self.stdout.write(self.style.SUCCESS(f"  Chapa accepted: {email}"))
                else:
                    error = response.get("error", {})
                    if "email" in str(error).lower():
                        self.stdout.write(
                            self.style.ERROR(f"  Chapa rejected email: {error}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  ? Other Chapa error: {error}")
                        )

            except ValueError as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Internal validation failed: {e}")
                )

        # Now test your actual user's email
        self.stdout.write(self.style.HTTP_INFO("\n" + "=" * 50))
        self.stdout.write(self.style.HTTP_INFO("Testing your actual users..."))

        users = User.objects.all()[:3]  # Test first 3 users

        for user in users:
            if user.email:
                self.stdout.write(f"\nUser {user.pk} ({user.username}): {user.email}")

                try:
                    validated_email = chapa_service._validate_email(user.email)
                    first_name = chapa_service._clean_name(
                        user.first_name or user.username
                    )
                    last_name = chapa_service._clean_name(user.last_name or "User")

                    success, response = chapa_service.initiate_payment(
                        amount=100,
                        email=validated_email,
                        first_name=first_name,
                        last_name=last_name,
                        phone_number="0912345678",
                        description="Real user test",
                    )

                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f"  User {user.pk} email works!")
                        )
                    else:
                        error = response.get("error", {})
                        self.stdout.write(
                            self.style.ERROR(
                                f"  ✗ User {user.pk} email failed: {error}"
                            )
                        )

                        # Suggest fixes
                        if "email" in str(error).lower():
                            domain = (
                                user.email.split("@")[1] if "@" in user.email else ""
                            )
                            suggested_email = f"{user.username}@gmail.com"
                            self.stdout.write(
                                f"     Suggestion: Try updating to {suggested_email}"
                            )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  Error testing user {user.pk}: {e}")
                    )

        # Recommendations
        self.stdout.write(self.style.HTTP_INFO("\n" + "=" * 50))
        self.stdout.write(self.style.HTTP_INFO("RECOMMENDATIONS:"))
        self.stdout.write(
            "1. Use mainstream email providers (Gmail, Yahoo, Hotmail, Outlook)"
        )
        self.stdout.write("2. Avoid custom domains that might not be recognized")
        self.stdout.write(
            "3. Ensure phone numbers are in 09xxxxxxxx or 07xxxxxxxx format"
        )
        self.stdout.write("4. Make sure user first_name and last_name are not empty")

        # Show the working payload format
        self.stdout.write(self.style.HTTP_INFO("\nWORKING PAYLOAD EXAMPLE:"))
        example_payload = {
            "amount": "100",
            "currency": "ETB",
            "email": "abebe.kebede@gmail.com",
            "first_name": "Abebe",
            "last_name": "Kebede",
            "phone_number": "0912345678",
            "tx_ref": "ALX_TRAVEL_12345678",
            "description": "Test payment",
        }

        import json

        self.stdout.write(json.dumps(example_payload, indent=2))
