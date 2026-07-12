from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
# <<<<<<< HEAD
from .models import CustomerUser
from django.contrib import admin
from .models import PaymentHistory,Transaction

# =======
from .models import CustomerUser, LoginHistory
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33


from .models import Tracker

# admin.site.register(CustomerUser)
class CustomerAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    list_display = ("email", "first_name", "last_name")

    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "gender",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "country",
                    "is_admin",
                    # "is_staff",
                    "is_client",
                    "is_applicant",
                    "is_employee_contract_signed",
                    "resume_file",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "gender",
                    "category",
                    "phone",
                    "address",
                    "city",
                    "state",
                    "country",
                    "is_admin",
                    "resume_file",
                )
            },
        ),
    )
    search_fields = ("email",)
    filter_horizontal = ()


class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time')
    list_filter = ('user', 'login_time', 'logout_time')
    search_fields = ('user__username',)



# Now register the new UserAdmin...
admin.site.register(CustomerUser, CustomerAdmin)
# admin.site.register(CustomerUser)

# Register your models here.
# <<<<<<< HEAD



# app/admin.py



@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "user",
        "amount",
        "currency",
        "provider",
        "status",
        "created_at",
    )

    list_filter = (
        "provider",
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "reference_code",
        "provider_payment_id",
        "provider_customer_id",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("User & Reference", {
            "fields": ("user", "purpose", "reference_code")
        }),
        ("Payment Details", {
            "fields": ("amount", "currency", "provider", "payment_method")
        }),
        ("Gateway Info", {
            "fields": ("provider_payment_id", "provider_customer_id", "provider_payload")
        }),
        ("Status & Dates", {
            "fields": ("status", "initiated_at", "completed_at")
        }),
        ("Financial Breakdown", {
            "fields": ("transaction_fee", "net_amount")
        }),
        ("Additional", {
            "fields": ("receipt_url", "notes")
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at")
        }),
    )
# =======
admin.site.register(LoginHistory, LoginHistoryAdmin)
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "department",
        "receiver",
        "phone",
        "type",
        "amount",
        "transaction_cost",
        "payment_method",
        "activity_date",
        "created_at",
    )

    list_filter = (
        "type",
        "payment_method",
        "department",
        "activity_date",
        "created_at",
    )

    search_fields = (
        "receiver",
        "phone",
        "description",
        "sender__email",
        "sender__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-activity_date",
        "-created_at",
    )

    date_hierarchy = "activity_date"
