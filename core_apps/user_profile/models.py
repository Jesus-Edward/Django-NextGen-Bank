from typing import Any

from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from core_apps.common.models import TimestampedModel
# Create your models here.

User = get_user_model()

class Profile(TimestampedModel):
    class Salutation(models.TextChoices):
        MR = ("mr", _("Mr"),)
        MRS = ("mrs", _("Mrs"),)
        MISS = ("miss", _("Miss"),)

    class Gender(models.TextChoices):
        MALE= ("male", _("Male"),)
        FEMALE= ("female", _("Female"),)

    class MaritalStatus(models.TextChoices):
        SINGLE = ("single", _("Single"),)
        MARRIED = ("married", _("Married"),)
        SEPERATED = ("seperated", _("Seperated"),)
        DIVORCED = ("divorced", _("Divorced"),)
        WIDOWED = ("widowed", _("Widowed"),)
        UNKNOWN = ("unknown", _("Unknown"),)

    class IndentificationMeans(models.TextChoices):
        DRIVERS_LICENSE = ("drivers_license", _("Drivers License"),)
        PASSPORT = ("passport", _("Passport"),)
        NATIONAL_ID = ("national_id", _("National ID"),)
        VOTERS_CARD = ("voters_card", _("Voters Card"),)

    class EmploymentStatus(models.TextChoices):
        SELF_EMPLOYED = ("self_employed", _("Self Employed"),)
        EMPLOYED = ("employed", _("Employed"),)
        UNEMPLOYED = ("unemployed", _("Unemployed"),)
        RETIRED = ("retired", _("Retired"),)
        STUDENT = ("student", _("Student"),)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    title = models.CharField(choices=Salutation.choices, default=Salutation.MR, max_length=10, verbose_name=_("Salutation"))
    gender = models.CharField(choices=Gender.choices, default=Gender.MALE, max_length=20, verbose_name=_("Gender"))
    marital_status = models.CharField(choices=MaritalStatus.choices, default=MaritalStatus.SINGLE, max_length=50, verbose_name=_("Marital Status"))
    identification_means = models.CharField(choices=IndentificationMeans.choices, default=IndentificationMeans.NATIONAL_ID, max_length=50, verbose_name=_("Means of Identification"))
    employment_status = models.CharField(choices=EmploymentStatus.choices, default=EmploymentStatus.SELF_EMPLOYED, max_length=50, verbose_name=_("Employment Status"))
    date_of_birth = models.DateField(verbose_name=_("Date of Birth"), default=settings.DEFAULT_BIRTH_DATE)
    country_of_birth = models.CharField(verbose_name=_("Country of Birth"), default=settings.DEFAULT_COUNTRY)
    place_of_birth = models.CharField(verbose_name=_("Place of Birth"), default="Unknown", max_length=50)
    id_issued_date = models.DateField(_("ID or Passport Issued Date"), default=settings.DEFAULT_DATE)
    id_expiry_date = models.DateField(_("ID or Passport Expiry Date"), default=settings.DEFAULT_EXPIRY_DATE)
    id_number = models.CharField(_("ID or Passport Number"), default=settings.DEFAULT_EXPIRY_DATE, max_length=50)
    nationality = models.CharField(_("Nationality"), default="Unknown", max_length=100)
    phone_number = PhoneNumberField(_("Phone Number"), max_length=30, default=settings.DEFAULT_PHONE_NUMBER, region="NG")
    address = models.CharField(_("Address"), max_length=150, default="Unknown")
    city = models.CharField(_("City"), default="Unknown", max_length=50)
    country = CountryField(_("Country"), default=settings.DEFAULT_COUNTRY, max_length=100)
    employer_name = models.CharField(_("Employer Name"), max_length=50, blank=True, null=True)
    annual_income = models.DecimalField(_("Annual Income"), default=0.0, decimal_places=2, max_digits=12)
    date_of_employment = models.DateField(_("Date of Employment"), blank=True, null=True)
    employer_address = models.CharField(_("Employer Address"), blank=True, null=True, max_length=150)
    employer_city = models.CharField(_("Employer City"), blank=True, null=True, max_length=100)
    employer_state = models.CharField(_("Employer City"), blank=True, null=True, max_length=100)
    photo = CloudinaryField(_("Photo"), blank=True, null=True)
    photo_url =  models.URLField(_("Photo URL"), blank=True, null=True)
    id_photo = CloudinaryField(_("ID Photo"), blank=True, null=True)
    id_photo_url = models.URLField(_("ID Photo URL"), blank=True, null=True)
    signature_photo = CloudinaryField(_("Signature Photo"), blank=True, null=True)
    signature_photo_url = models.URLField(_("Signature Photo URL"), blank=True, null=True)

    def clean(self) -> None:
        super().clean()
        if self.id_issued_date and self.id_expiry_date:
            if self.id_expiry_date <= self.id_issued_date:
                raise ValidationError(_("ID expiry date must come after the issued date."))

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def is_complete_with_next_of_kin(self):
        required_fields = [
            self.gender,
            self.date_of_birth,
            self.title,
            self.country_of_birth,
            self.place_of_birth,
            self.marital_status,
            self.employment_status,
            self.identification_means,
            self.id_issued_date,
            self.id_expiry_date,
            self.nationality,
            self.phone_number,
            self.city,
            self.country,
            self.photo,
            self.id_photo,
            self.signature_photo
        ]
        return all(required_fields) and self.next_of_kin.exists()

    def __str__(self):
        return f"{self.title} {self.user.first_name}'s Profile"

class NextOfKin(TimestampedModel):
    class Salutation(models.TextChoices):
        MR = ("mr", _("Mr"),)
        MRS = ("mrs", _("Mrs"),)
        MISS = ("miss", _("Miss"),)

    class Gender(models.TextChoices):
        MALE= ("male", _("Male"),)
        FEMALE= ("female", _("Female"),)

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="next_of_kin")
    title = models.CharField(choices=Salutation.choices, default=Salutation.MR, max_length=10, verbose_name=_("Salutation"))
    first_name = models.CharField(_("First Name"), max_length=50)
    last_name = models.CharField(_("Last Name"), max_length=50)
    other_name = models.CharField(_("Other Name"), max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(_("Date of Birth"))
    gender = models.CharField(choices=Gender.choices, default=Gender.MALE, max_length=20, verbose_name=_("Gender"))
    relationship = models.CharField(_("Relationship"), max_length=50)
    email = models.EmailField(_("Email"), max_length=150, db_index=True)
    phone_number = PhoneNumberField(_("Phone Number"))
    address = models.CharField(_("Address"), max_length=150)
    city = models.CharField(_("City"), max_length=50)
    country = CountryField(_("Country"), max_length=100)
    is_primary = models.BooleanField(_("Is Primary Next of Kin"), default=False)

    def clean(self) -> None:
        super().clean()
        if self.is_primary:
            primary_kin = NextOfKin.objects.filter(profile=self.profile, is_primary=True).exclude(pk=self.pk)
            if primary_kin.exists():
                raise ValidationError(_("There can only be one Primary Next of Kin"))
            
    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Next of Kin for {self.profile.user.full_name}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "is_primary"],
                condition=models.Q(is_primary=True),
                name="unique_next_of_kin"
            )
        ]
