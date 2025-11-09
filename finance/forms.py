from django import forms
from .models import Default_Payment_Fees


class Default_Payment_Fees_form(forms.ModelForm):
    class Meta:
        model = Default_Payment_Fees
        fields = [
            "job_down_payment_per_month",
            "job_plan_hours_per_month",
            "student_down_payment_per_month",
            "student_bonus_payment_per_month",
        ]
