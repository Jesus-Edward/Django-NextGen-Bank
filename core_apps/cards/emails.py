from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger


def send_virtual_card_topup_email(user, virtual_card, amount, new_balance):
    subject = _("Your Virtual Card has been topped up")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [user.email]

    context = {
        "user_full_name": user.full_name,
        "amount": amount,
        "card_last_four": virtual_card.card_number[-4:],
        "new_balance": new_balance,
        "site_name": settings.SITE_NAME,
    }

    html_email = render_to_string("emails/virtual_card_topup.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(
            f"Virtual Card top-up confirmation email sent to {user.email} successfully"
        )
    except Exception as e:
        logger.error(
            f"Failed to send Virtual Card top-up confirmation email to {user.email}: Error: {str(e)}"
        )
