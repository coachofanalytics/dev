

from django.contrib import admin
from .models import Signup
@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("firstname", "lastname", "email", "phone")
    search_fields = ("firstname", "lastname", "email", "phone")
from django.contrib import admin
from .models import VisaApplication


@admin.register(VisaApplication)
class VisaApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "email",
        "visa_type",
        "destination_country",
        "created_at"
    )

    list_filter = ("visa_type", "destination_country")

    search_fields = ("first_name", "last_name", "email", "passport_number")


from django.contrib import admin
from .models import Consultation, PreAssessment
@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('application_number','service_type', 'consultation_mode', 'date', 'time', 'status')
    list_filter = ('service_type', 'consultation_mode', 'status')
    search_fields = ('application_number', 'user__username', 'user__email')

from django.contrib import admin
from .models import PreAssessment

@admin.register(PreAssessment)
class PreAssessmentAdmin(admin.ModelAdmin):
    list_display = ('country', 'purpose', 'rejected_before', 'created_at')
    list_filter = ('country', 'purpose', 'rejected_before')
    search_fields = ('country', 'purpose')

from django.contrib import admin
from .models import EligibilityRule,CitizenshipPath,Applicant

admin.site.register(EligibilityRule)
admin.site.register(CitizenshipPath)
admin.site.register(Applicant)

from django.contrib import admin
from .models import AttorneyRequest

@admin.register(AttorneyRequest)
class AttorneyRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'country', 'issue_type', 'created_at')
    list_filter = ('issue_type', 'country', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    ordering = ('-created_at',)