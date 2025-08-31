
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Payment, Booking
from listings.chapa_service import ChapaService
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Troubleshoot payment issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tx-ref',
            type=str,
            help='Transaction reference to troubleshoot',
        )
        parser.add_argument(
            '--payment-id',
            type=str,
            help='Payment ID to troubleshoot',
        )
        parser.add_argument(
            '--list-recent',
            action='store_true',
            help='List recent payments',
        )

    def handle(self, *args, **options):
        if options['list_recent']:
            self.list_recent_payments()
        elif options['tx_ref']:
            self.troubleshoot_by_tx_ref(options['tx_ref'])
        elif options['payment_id']:
            self.troubleshoot_by_payment_id(options['payment_id'])
        else:
            self.stdout.write(self.style.ERROR('Please provide --tx-ref, --payment-id, or --list-recent'))

    def list_recent_payments(self):
        """List recent payments for troubleshooting."""
        self.stdout.write(self.style.HTTP_INFO('Recent payments (last 10):'))
        
        payments = Payment.objects.select_related(
            'booking', 'booking__user', 'booking__listing'
        ).order_by('-created_at')[:10]
        
        for payment in payments:
            self.stdout.write(f"\n--- Payment {payment.id} ---")
            self.stdout.write(f"TX Ref: {payment.booking_reference}")
            self.stdout.write(f"Status: {payment.status}")
            self.stdout.write(f"Amount: {payment.amount} {payment.currency}")
            self.stdout.write(f"Customer: {payment.customer_name} ({payment.customer_email})")
            self.stdout.write(f"Booking: {payment.booking.listing.title}")
            self.stdout.write(f"User: {payment.booking.user.username}")
            self.stdout.write(f"Created: {payment.created_at}")
            if payment.checkout_url:
                self.stdout.write(f"Checkout URL: {payment.checkout_url}")

    def troubleshoot_by_tx_ref(self, tx_ref):
        """Troubleshoot specific payment by transaction reference."""
        self.stdout.write(f"Troubleshooting payment: {tx_ref}")
        
        try:
            payment = Payment.objects.select_related(
                'booking', 'booking__user', 'booking__listing'
            ).get(booking_reference=tx_ref)
            
            self.display_payment_details(payment)
            self.verify_with_chapa(payment)
            
        except Payment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Payment with tx_ref {tx_ref} not found"))

    def troubleshoot_by_payment_id(self, payment_id):
        """Troubleshoot specific payment by ID."""
        self.stdout.write(f"Troubleshooting payment ID: {payment_id}")
        
        try:
            payment = Payment.objects.select_related(
                'booking', 'booking__user', 'booking__listing'
            ).get(id=payment_id)
            
            self.display_payment_details(payment)
            self.verify_with_chapa(payment)
            
        except Payment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Payment with ID {payment_id} not found"))

    def display_payment_details(self, payment):
        """Display comprehensive payment details."""
        self.stdout.write(self.style.HTTP_INFO('\n=== PAYMENT DETAILS ==='))
        self.stdout.write(f"Payment ID: {payment.id}")
        self.stdout.write(f"Transaction Reference: {payment.booking_reference}")
        self.stdout.write(f"Transaction ID: {payment.transaction_id}")
        self.stdout.write(f"Status: {payment.status}")
        self.stdout.write(f"Amount: {payment.amount} {payment.currency}")
        self.stdout.write(f"Payment Method: {payment.payment_method or 'Not specified'}")
        
        self.stdout.write(f"\nCustomer Information:")
        self.stdout.write(f"  Name: {payment.customer_name}")
        self.stdout.write(f"  Email: {payment.customer_email}")
        self.stdout.write(f"  Phone: {payment.customer_phone or 'Not provided'}")
        
        self.stdout.write(f"\nBooking Information:")
        self.stdout.write(f"  Booking ID: {payment.booking.id}")
        self.stdout.write(f"  Listing: {payment.booking.listing.title}")
        self.stdout.write(f"  Check-in: {payment.booking.start_date}")
        self.stdout.write(f"  Check-out: {payment.booking.end_date}")
        self.stdout.write(f"  Booking Status: {payment.booking.status}")
        self.stdout.write(f"  User: {payment.booking.user.username} ({payment.booking.user.email})")
        
        self.stdout.write(f"\nPayment Timeline:")
        self.stdout.write(f"  Created: {payment.created_at}")
        self.stdout.write(f"  Updated: {payment.updated_at}")
        self.stdout.write(f"  Completed: {payment.completed_at or 'Not completed'}")
        
        if payment.checkout_url:
            self.stdout.write(f"\nCheckout URL: {payment.checkout_url}")
        
        # Show Chapa response data if available
        if payment.chapa_response_data:
            self.stdout.write(f"\nStored Chapa Response:")
            self.stdout.write(json.dumps(payment.chapa_response_data, indent=2, default=str))

    def verify_with_chapa(self, payment):
        """Verify payment status with Chapa API."""
        self.stdout.write(self.style.HTTP_INFO('\n=== CHAPA VERIFICATION ==='))
        
        chapa_service = ChapaService()
        success, response = chapa_service.verify_payment(payment.booking_reference)
        
        if success:
            self.stdout.write(self.style.SUCCESS("Chapa verification successful"))
            
            chapa_data = response.get("data", {})
            chapa_status = chapa_data.get("status", "").lower()
            
            self.stdout.write(f"\nChapa Response:")
            self.stdout.write(json.dumps(response, indent=2, default=str))
            
            self.stdout.write(f"\n--- Status Comparison ---")
            self.stdout.write(f"Database Status: {payment.status}")
            self.stdout.write(f"Chapa Status: {chapa_status}")
            
            if chapa_status == payment.status.lower():
                self.stdout.write(self.style.SUCCESS("✓ Statuses match"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Status mismatch detected"))
                
                # Suggest actions
                self.stdout.write(f"\nRecommended Actions:")
                if chapa_status == "success" and payment.status != "completed":
                    self.stdout.write("- Update payment status to 'completed'")
                    self.stdout.write("- Update booking status to 'confirmed'")
                    self.stdout.write("- Send confirmation email to customer")
                elif chapa_status in ["failed", "cancelled"] and payment.status not in ["failed", "cancelled"]:
                    self.stdout.write(f"- Update payment status to '{chapa_status}'")
                    self.stdout.write("- Send failure notification to customer")
                elif chapa_status == "pending" and payment.status == "pending":
                    self.stdout.write("- Consider updating to 'processing' status")
                    self.stdout.write("- Monitor and check again later")
                
        else:
            self.stdout.write(self.style.ERROR("Chapa verification failed"))
            self.stdout.write(f"Error: {response.get('error', 'Unknown error')}")
            
            if response.get('status_code') == 404:
                self.stdout.write("This might indicate the payment doesn't exist in Chapa's system")
            elif response.get('status_code') == 401:
                self.stdout.write("Authentication failed - check your Chapa secret key")

    def style_json(self, data):
        """Pretty print JSON data."""
        return json.dumps(data, indent=2, default=str)