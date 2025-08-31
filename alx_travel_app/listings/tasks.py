import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags



logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_payment_confirmation_email(self, booking_id, payment_id):
    """
    Send payment confirmation email to user
    """
    try:
        from .models import Booking, Payment

        booking = Booking.objects.get(id=booking_id)
        payment = Payment.objects.get(id=payment_id)

        # Prepare email context
        context = {
            "user_name": f"{booking.user.first_name} {booking.user.last_name}",
            "booking": booking,
            "payment": payment,
            "listing": booking.listing,
            "nights": (booking.end_date - booking.start_date).days,
        }

        # Create email content
        subject = f"Payment Confirmation - Booking #{booking.pk}"

        # HTML email template
        html_message = f"""
        <html>
        <body>
            <h2>Payment Confirmation</h2>
            <p>Dear {context["user_name"]},</p>
            
            <p>Your payment has been successfully processed!</p>
            
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Listing:</strong> {booking.listing.title}</li>
                <li><strong>Check-in:</strong> {booking.start_date}</li>
                <li><strong>Check-out:</strong> {booking.end_date}</li>
                <li><strong>Nights:</strong> {context["nights"]}</li>
                <li><strong>Total Amount:</strong> {payment.amount} {payment.currency}</li>
            </ul>
            
            <h3>Payment Details:</h3>
            <ul>
                <li><strong>Transaction ID:</strong> {payment.transaction_id}</li>
                <li><strong>Reference:</strong> {payment.booking_reference}</li>
                <li><strong>Status:</strong> {payment.status}</li>
                <li><strong>Payment Date:</strong> {payment.completed_at or payment.updated_at}</li>
            </ul>
            
            <p>Thank you for choosing ALX Travel App!</p>
            
            <p>Best regards,<br>ALX Travel Team</p>
        </body>
        </html>
        """

        # Plain text version
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Payment confirmation email sent for booking {booking_id}")
        return f"Email sent successfully for booking {booking_id}"

    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying email send (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=e)
        else:
            logger.error("Max retries reached for email send task")
            return f"Failed to send email after {self.max_retries} attempts"


@shared_task
def send_payment_failure_email(booking_id, payment_id, error_message=""):
    """
    Send payment failure notification email
    """
    try:
        from .models import Booking, Payment

        booking = Booking.objects.get(id=booking_id)
        payment = Payment.objects.get(id=payment_id)

        subject = f"Payment Failed - Booking #{booking.pk}"

        html_message = f"""
        <html>
        <body>
            <h2>Payment Failed</h2>
            <p>Dear {booking.user.first_name} {booking.user.last_name},</p>
            
            <p>Unfortunately, your payment could not be processed.</p>
            
            <h3>Booking Details:</h3>
            <ul>
                <li><strong>Listing:</strong> {booking.listing.title}</li>
                <li><strong>Amount:</strong> {payment.amount} {payment.currency}</li>
                <li><strong>Reference:</strong> {payment.booking_reference}</li>
            </ul>
            
            <p>Please try again or contact our support team if the issue persists.</p>
            
            {f"<p><strong>Error:</strong> {error_message}</p>" if error_message else ""}
            
            <p>Best regards,<br>ALX Travel Team</p>
        </body>
        </html>
        """

        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Payment failure email sent for booking {booking_id}")
        return f"Payment failure email sent for booking {booking_id}"

    except Exception as e:
        logger.error(f"Failed to send payment failure email: {str(e)}")
        return f"Failed to send payment failure email: {str(e)}"





@shared_task
def send_booking_confirmation_email(to_email, booking_id):
    subject = "Booking Confirmation"
    message = f"Thank you for your booking! Your booking ID is {booking_id}."
    from_email = None  # will use DEFAULT_FROM_EMAIL
    recipient_list = [to_email]

    send_mail(subject, message, from_email, recipient_list)

    return f"Booking confirmation email sent to {to_email} for booking {booking_id}"
