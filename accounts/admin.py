from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
from .models import  UserGroups, PaymentHistory, Tracker, LoginHistory

# Registering CustomerUser with Django's built-in UserAdmin for a clean UI
# @admin.register(CustomerUser)
# class CustomUserAdmin(UserAdmin):
#     # Add your custom fields to the admin display and edit panels
#     fieldsets = UserAdmin.fieldsets + (
#         ("Additional Info", {
#             "fields": (
#                 "gender", "phone", "address", "city", "state", 
#                 "zipcode", "country", "category", "sub_category",
#                 "is_admin", "is_client", "is_applicant", 
#                 "is_employee_contract_signed", "resume_file"
#             )
#         }),
#     )
#     list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_client", "is_applicant")
#     list_filter = ("is_staff", "is_client", "is_applicant", "category", "is_active")

# Registering the rest of your models normally
admin.site.register(UserGroups)
admin.site.register(PaymentHistory)
admin.site.register(Tracker)
admin.site.register(LoginHistory)