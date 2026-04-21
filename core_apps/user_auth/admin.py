from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _
from .forms import UserChangeForm, UserCreationForm


# Register your models here.
# @admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
        "roles",
    )
    list_display_links = (
        "email",
        "username",
    )
    list_filter = (
        "email",
        "is_staff",
        "is_active",
        "roles",
    )
    readonly_fields = ("last_login", "date_joined",)
    search_fields = ["first_name", "last_name", "email", "username"]
    ordering = ["email"]
    fieldsets = (
        (
            _("Login Credentials"),
            {
                "fields": (
                    "email",
                    "username",
                    "password",
                )
            },
        ),
        (
            _("Personal Info"),
            {
                "fields": (
                    "first_name",
                    "middle_name",
                    "last_name",
                    "id_no",
                    "roles",
                )
            },
        ),
        (
            _("Account Status"),
            {
                "fields": (
                    "account_status",
                    "failed_login_attempts",
                    "last_failed_login",
                )
            },
        ),
        (
            _("Security"),
            {
                "fields": (
                    "security_question",
                    "security_answer",
                )
            },
        ),
        (
            _("Permissions and Groups"),
            {
                "fields": (
                    "is_superuser",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important Dates"),
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)
