from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger

def send_account_creation_email(user, bank_account):
    subject = _("Your New Bank Account has been Created")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [user.email]

    context = {
        "user": user,
        "account": bank_account,
        "site_name": settings.SITE_NAME,
        "expiry_time": settings.OTP_EXPIRATION,
    }

    html_email = render_to_string("emails/account_number_created.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(f"Account creation confirmation email sent to {user.email} successfully")
    except Exception as e:
        logger.error(f"Failed to send Account creation confirmation to {user.email}: Error: {str(e)}")
