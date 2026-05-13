from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.accounts.models import BankAccount
from core_apps.common.models import TimestampedModel

User = get_user_model()

class VirtualCards(TimestampedModel):
    class CardStatus(models.TextChoices):
        ACTIVE = ("active", _("Active"),)
        INACTIVE = ("inactive", _("Inactive"),)
        BLOCKED = ("blocked", _("Blocked"))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="virtual_cards")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="bank_account")
    card_number = models.CharField(_("Card Number"), max_length=20, unique=True)
    expiry_date = models.DateTimeField(_("Expiry Date"))
    cvv = models.CharField(_("CVV Number"), max_length=16, unique=True)
    balance = models.DecimalField(_("Balance"), max_digits=10, decimal_places=2, default=0)
    status = models.CharField(_("Status"), max_length=20, choices=CardStatus.choices, default=CardStatus.ACTIVE)

    class Meta:
        verbose_name = _("Virtual Card")
        verbose_name_plural = _("Virtual Cards")

    def __str__(self):
        return f"Virtual Card {self.card_number} for user {self.user.full_name}"
