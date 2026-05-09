from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger
from core_apps.accounts.models import BankAccount

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
        logger.error(f"Failed to send Account creation confirmation email to {user.email}: Error: {str(e)}")

def send_account_activation_email(account: BankAccount):
    subject = _("Your Bank Account has been Activated")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [account.user.email]

    context = {
        "account": account,
        "site_name": settings.SITE_NAME,
    }

    html_email = render_to_string("emails/bank_account_activated.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(f"Account activvation email sent to {account.user.email} successfully")
    except Exception as e:
        logger.error(f"Failed to send Account activation email to {account.user.email}: Error: {str(e)}")

def send_deposit_email(user, user_email, amount, currency, new_balance, account_number):
    subject = _("Deposit Confirmation")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [user_email]

    context = {
        "user": user,
        "amount": amount,
        "currency": currency,
        "account_number": account_number,
        "new_balance": new_balance,
        "site_name": settings.SITE_NAME,
    }

    html_email = render_to_string("emails/deposit_confirmation.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(f"Deposit Confirmation email sent to {user_email} successfully")
    except Exception as e:
        logger.error(f"Failed to send Deposit Confirmation email to {user_email}: Error: {str(e)}")

def send_withdrawal_email(user, user_email, amount, currency, new_balance, account_number):
    subject = _("Withdrawal Confirmation")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [user_email]

    context = {
        "user": user,
        "amount": amount,
        "currency": currency,
        "account_number": account_number,
        "new_balance": new_balance,
        "site_name": settings.SITE_NAME,
    }

    html_email = render_to_string("emails/withdrawal_confirmation.html", context=context)
    plain_email = strip_tags(html_email)
    email = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    email.attach_alternative(html_email, "text/html")

    try:
        email.send()
        logger.info(f"Withdrawal Confirmation email sent to {user_email} successfully")
    except Exception as e:
        logger.error(f"Failed to send Withdrawal Confirmation email to {user_email}: Error: {str(e)}")

def send_transferl_email(sender_name, sender_email, sender_acc_num, sender_new_bal, receiver_name, receiver_email, receiver_acc_num, receiver_new_bal, amount, currency):
    subject = _("Transfer Confirmation")
    from_email = settings.DEFAULT_FROM_EMAIL

    common_context = {
        "amount": amount,
        "currency": currency,
        "sender_account_number": sender_acc_num,
        "receiver_account_number": receiver_acc_num,
        "sender_name": sender_name,
        "receiver_name": receiver_name,
        "site_name": settings.SITE_NAME,
    }

    sender_context = {
        **common_context,
        "user": sender_name,
        "is_sender": True,
        "new_balance": sender_new_bal
    }

    sender_html_email = render_to_string("emails/transfer_receipt.html", context=sender_context)
    sender_plain_email = strip_tags(sender_html_email)
    sender_email_obj = EmailMultiAlternatives(
        subject=subject,
        body=sender_plain_email,
        from_email=from_email,
        to=[sender_email],
    )
    sender_email_obj.attach_alternative(sender_html_email, "text/html")

    receiver_context = {
        **common_context,
        "user": receiver_name,
        "is_sender": False,
        "new_balance": receiver_new_bal
    }

    receiver_html_email = render_to_string("emails/transfer_receipt.html", context=receiver_context)
    receiver_plain_email = strip_tags(receiver_html_email)
    receiver_email_obj = EmailMultiAlternatives(
        subject=subject,
        body=receiver_plain_email,
        from_email=from_email,
        to=[receiver_email],
    )
    receiver_email_obj.attach_alternative(receiver_html_email, "text/html")

    try:
        sender_email_obj.send()
        receiver_email_obj.send()
        logger.info(f"Transfer Confirmation email sent to the sender: {sender_email} and receiver: {receiver_email} successfully")
    except Exception as e:
        logger.error(f"Failed to send Transfer Confirmation email to both the sender: {sender_email} and the receiver: {receiver_email}: Error: {str(e)}")


def send_transfer_otp_email(email, otp):
    subject = _("Your Transfer OTP Code")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [email]

    context = {
        "otp": otp,
        "site_name": settings.SITE_NAME,
        "expiry_time": settings.OTP_EXPIRATION,
    }

    html_email = render_to_string("emails/transfer_otp_email.html", context=context)
    plain_email = strip_tags(html_email)
    emails = EmailMultiAlternatives(
        subject=subject, body=plain_email, from_email=from_email, to=recipient_email
    )
    emails.attach_alternative(html_email, "text/html")

    try:
        emails.send()
        logger.info(f"Transfer OTP sent to {email} successfully")
    except Exception as e:
        logger.error(f"Failed to send Transfer OTP to {email}: Error: {str(e)}")
