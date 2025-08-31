
import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from listings.chapa_service import ChapaService
from listings.models import Payment


class Command(BaseCommand):
    help = "Check and update payment statuses from Chapa"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tx-ref",
            type=str,
            help="Check specific transaction reference",
        )
        parser.add_argument(
            "--pending-only",
            action="store_true",
            help="Check only pending/processing payments",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )

    def handle(self, *args, **options):
        chapa_service = ChapaService()
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        if options["tx_ref"]:
            # Check specific payment
            self.check_specific_payment(options["tx_ref"], chapa_service, dry_run)
        elif options["pending_only"]:
            # Check only pending/processing payments
            self.check_pending_payments(chapa_service, dry_run)
        else:
            # Check all recent payments
            self.check_recent_payments(chapa_service, dry_run)

    def check_specific_payment(self, tx_ref, chapa_service, dry_run):
        """Check a specific payment by transaction reference."""
        self.stdout.write(f"Checking payment: {tx_ref}")

        try:
            payment = Payment.objects.select_related(
                "booking", "booking__user", "booking__listing"
            ).get(booking_reference=tx_ref)

            self.stdout.write("Found payment:")
            self.stdout.write(f"  ID: {payment.id}")
            self.stdout.write(f"  Current Status: {payment.status}")
            self.stdout.write(f"  Amount: {payment.amount} {payment.currency}")
            self.stdout.write(
                f"  Customer: {payment.customer_name} ({payment.customer_email})"
            )
            self.stdout.write(f"  Booking: {payment.booking.listing.title}")
            self.stdout.write(f"  Created: {payment.created_at}")

            # Verify with Chapa
            success, response = chapa_service.verify_payment(tx_ref)

            if success:
                chapa_data = response.get("data", {})
                chapa_status = chapa_data.get("status", "").lower()

                self.stdout.write(f"\nChapa Status: {chapa_status}")
                self.stdout.write(
                    f"Chapa Response: {json.dumps(chapa_data, indent=2, default=str)}"
                )

                if chapa_status != payment.status.lower():
                    self.stdout.write(self.style.WARNING("\nStatus mismatch!"))
                    self.stdout.write(f"  Database: {payment.status}")
                    self.stdout.write(f"  Chapa: {chapa_status}")

                    if not dry_run:
                        self.update_payment_status(payment, chapa_status, chapa_data)
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Would update to: {chapa_status}")
                        )
                else:
                    self.stdout.write(self.style.SUCCESS("Status is in sync"))
            else:
                self.stdout.write(
                    self.style.ERROR(f"Chapa verification failed: {response}")
                )

        except Payment.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Payment with tx_ref {tx_ref} not found")
            )

    def check_pending_payments(self, chapa_service, dry_run):
        """Check all pending and processing payments."""
        pending_payments = Payment.objects.filter(
            status__in=["pending", "processing"]
        ).select_related("booking", "booking__user", "booking__listing")

        self.stdout.write(
            f"Found {pending_payments.count()} pending/processing payments"
        )

        updated_count = 0

        for payment in pending_payments:
            self.stdout.write(f"\nChecking: {payment.booking_reference}")

            success, response = chapa_service.verify_payment(payment.booking_reference)

            if success:
                chapa_data = response.get("data", {})
                chapa_status = chapa_data.get("status", "").lower()

                self.stdout.write(
                    f"  Database: {payment.status} -> Chapa: {chapa_status}"
                )

                if chapa_status != payment.status.lower():
                    if not dry_run:
                        self.update_payment_status(payment, chapa_status, chapa_data)
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  Would update to: {chapa_status}")
                        )
                        updated_count += 1
                else:
                    self.stdout.write("  In sync")
            else:
                self.stdout.write(
                    self.style.ERROR(f"  Verification failed: {response.get('error')}")
                )

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"\nUpdated {updated_count} payments"))
        else:
            self.stdout.write(
                self.style.WARNING(f"\nWould update {updated_count} payments")
            )

    def check_recent_payments(self, chapa_service, dry_run):
        """Check payments from the last 24 hours."""
        since = timezone.now() - timezone.timedelta(hours=24)
        recent_payments = Payment.objects.filter(created_at__gte=since).select_related(
            "booking", "booking__user", "booking__listing"
        )

        self.stdout.write(
            f"Found {recent_payments.count()} payments from last 24 hours"
        )

        for payment in recent_payments:
            self.stdout.write(f"\n{payment.booking_reference} ({payment.status})")

            success, response = chapa_service.verify_payment(payment.booking_reference)

            if success:
                chapa_data = response.get("data", {})
                chapa_status = chapa_data.get("status", "").lower()

                if chapa_status != payment.status.lower():
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Status mismatch: {payment.status} -> {chapa_status}"
                        )
                    )
                    if not dry_run:
                        self.update_payment_status(payment, chapa_status, chapa_data)
                else:
                    self.stdout.write("  In sync")

    def update_payment_status(self, payment, chapa_status, chapa_data):
        """Update payment status based on Chapa response."""
        old_status = payment.status

        if chapa_status == "success":
            payment.status = "completed"
            payment.completed_at = timezone.now()
            payment.booking.status = "confirmed"
            payment.booking.save()

            self.stdout.write(self.style.SUCCESS("  Updated to completed"))

        elif chapa_status in ["failed", "cancelled"]:
            payment.status = chapa_status
            self.stdout.write(self.style.ERROR(f"  Updated to {chapa_status}"))

        elif chapa_status == "pending":
            if payment.status == "pending":
                payment.status = "processing"
                self.stdout.write("  Updated to processing")

        # Update response data
        payment.chapa_response_data.update({"data": chapa_data})
        payment.save()

        self.stdout.write(f"  Status changed: {old_status} -> {payment.status}")
