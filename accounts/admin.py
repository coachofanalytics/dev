from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomerUser, LoginHistory,All_transaction,Transaction,PaymentInformation,Payment_History


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
admin.site.register(LoginHistory, LoginHistoryAdmin)
admin.site.register(All_transaction)
admin.site.register(Transaction)
class PaymentInformationAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer_id", "payment_fees", "down_payment", 
        "student_bonus", "plan", "payment_method", "contract_submitted_date"
    )



@admin.register(Payment_History)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'payment_fees',
        'down_payment',
        'student_bonus',
        'fee_balance',
        'plan',
        'payment_method',
        'contract_submitted_date',
    )
    search_fields = ('customer__first_name', 'customer__last_name', 'payment_method')
    list_filter = ('payment_method', 'plan', 'contract_submitted_date')
    ordering = ('-contract_submitted_date',)


