from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .emails import send_email_locked_account
from .managers import UserManager
import uuid


# Create your models here.
class User(AbstractUser):
    class SecurityQuestion(models.TextChoices):
        MAIDEN_NAME = (
            (
                "maiden_name",
                _("What is your mother's maiden name?"),
            ),
        )
        BIRTH_CITY = (
            (
                "birth_city",
                _("What city were you born?"),
            ),
        )
        CHILDHOOD_FRIEND = (
            (
                "best_friend_name",
                _("What is your childhood friend's name?"),
            ),
        )
        FAVOURITE_CLOUR = (
            "favourite_colour",
            _("What is your favourite colour?"),
        )

    class AccountStatus(models.TextChoices):
        ACTIVE = (
            (
                "active",
                _("Active"),
            ),
        )
        LOCKED = (
            (
                "locked",
                _("Locked"),
            ),
        )

    class Roles(models.TextChoices):
        CUSTOMER = ("customer", _("Customer"))
        ACCOUNT_EXECUTIVE = (
            "account_executive",
            _("Account Executive"),
        )
        TELLER = (
            (
                "teller",
                _("Teller"),
            ),
        )
        BRANCH_MANAGER = (
            "branch_manager",
            _("Branch Manager"),
        )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(_("Username"), max_length=15, unique=True)
    security_question = models.CharField(
        _("Security Question"), max_length=100, choices=SecurityQuestion.choices
    )
    security_answer = models.CharField(_("Security Question Answer"), max_length=50)
    email = models.EmailField(_("Email"), max_length=100, unique=True, db_index=True)
    first_name = models.CharField(_("First Name"), blank=True, max_length=50)
    middle_name = models.CharField(
        _("Middle Name"), blank=True, max_length=50, null=True
    )
    last_name = models.CharField(_("Last Name"), blank=True, max_length=50)
    id_no = models.PositiveBigIntegerField(_("ID No"), unique=True)
    account_status = models.CharField(
        _("Account Status"), max_length=50, choices=AccountStatus.choices
    )
    roles = models.CharField(_("User Role"), max_length=50, choices=Roles.choices)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    otp = models.CharField(_("OTP"), max_length=6, blank=True)
    otp_expiry_time = models.DateTimeField(_("OTP Expiry Time"), blank=True, null=True)

    objects = (
        UserManager()
    )  # object is a special attribute that represents the default manager for a model in django

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "id_no",
        "security_question",
        "security_answer",
    ]

    def set_otp(self, otp: str) -> None:
        self.otp = otp
        self.otp_expiry_time = timezone.now() + settings.OTP_EXPIRATION
        self.save()

    def verify_otp(self, otp: str) -> bool:
        if self.otp == otp and self.otp_expiry_time > timezone.now():
            self.otp = ""
            self.otp_expiry_time = None
            self.save()
            return True
        return False

    def handle_failed_login_attempt(self) -> None:
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        if self.failed_login_attempts >= settings.LOGIN_ATTEMPTS:
            self.account_status = self.AccountStatus.LOCKED
            self.save()
            send_email_locked_account(self)
        self.save()

    def reset_failed_login_attempts(self) -> None:
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_status = self.AccountStatus.ACTIVE
        self.save()

    def unlock_locked_account(self):
        if self.account_status == self.AccountStatus.LOCKED:
            self.account_status = self.AccountStatus.ACTIVE
            self.failed_login_attempts = 0
            self.last_failed_login = None
            self.save()

    @property
    def is_locked_out(self) -> bool:
        if self.account_status == self.AccountStatus.LOCKED:
            if (
                self.last_failed_login
                and (timezone.now() - self.last_failed_login) > settings.LOGOUT_DURATION
            ):
                self.unlock_locked_account()
                return False
            return True
        return False

    @property
    def full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.title().strip()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]

    def has_role(self, role_name: str) -> bool:
        return hasattr(self, "roles") and self.roles == role_name

    def __str__(self):
        return f"{self.full_name} - {self.get_roles_display()}"
