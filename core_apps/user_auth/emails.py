from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger


def send_email_otp(email, otp):
    subject = _("Your Login OTP Code")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [email]

    context = {
        "otp": otp,
        "site_name": settings.SITE_NAME,
        "expiry_time": settings.OTP_EXPIRATION,
    }

    html_email = render_to_string("emails/otp_email.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(f"OTP sent to {email} successfully")
    except Exception as e:
        logger.error(f"Failed to send OTP to {email}: Error: {str(e)}")


def send_email_locked_account(self):
    subject = _("Your account has been locked")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [self.email]

    context = {
        "user": self,
        "site_name": settings.SITE_NAME,
        "logout_duration": int(settings.LOGOUT_DURATION.total_seconds() // 60),
    }

    html_email = render_to_string("emails/account_locked.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(f"Email sent to {self.email} successfully")
    except Exception as e:
        logger.error(f"Failed to send email to {self.email}: Error: {str(e)}")
