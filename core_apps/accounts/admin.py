from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import BankAccount
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        "account_number",
        "user",
        "currency",
        "account_type",
        "account_balance",
        "account_status",
        "is_primary",
        "kyc_verified",
        "get_verified_by",
    ]
    list_filter = [
        "currency",
        "account_type",
        "account_status",
        "is_primary",
        "kyc_submitted",
        "kyc_verified",
    ]
    search_fields = [
        "account_number",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]
    readonly_fields = ["account_number", "created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "account_number",
                    "account_balance",
                    "currency",
                    "account_type",
                    "is_primary",
                )
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "account_status",
                    "kyc_submitted",
                    "kyc_verified",
                    "verification_date",
                    "fully_activated",
                    "verification_notes",
                )
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_verified_by(self, obj):
        return obj.verified_by.full_name if obj.verified_by else "-"

    get_verified_by.short_description = "Verified By"
    get_verified_by.admin_order_field = "verified_by__first_name"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        return qs.filter(verified_by=request.user)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return request.user.is_superuser or obj.verified_by == request.user

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "verified_by":  # db_field.name is the name of the ForeignKey field in BankAccount model that is being edited in the admin interface
            kwargs["queryset"] = User.objects.filter(is_staff=True) # Filter the queryset to include only staff users (branch managers) who can verify accounts and set the queryset for the "verified_by" field in the admin form to this filtered queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs) # Call the parent method to get the default form field for the ForeignKey and return it with the modified queryset for the "verified_by" field 
