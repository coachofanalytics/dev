from django import forms
from .models import OverBoughtSold,PaymentInformation

class OverBoughtSoldForm(forms.ModelForm):
    class Meta:
        model = OverBoughtSold
        fields = [
            "symbol", "description", "last", "volume", "RSI",
            "EPS", "PE", "rank", "profit_margins"
        ]



from django import forms
from .models import PaymentInformation

class PaymentInformationForm(forms.ModelForm):
    class Meta:
        model = PaymentInformation
        fields = [
            "customer",
            "total_fees",
            "down_payment",
            "student_bonus",
            "payment_method",
            "contract_submitted_date",
            "client_signature",
            "company_rep",
            "is_active",
            "is_tested",
            "is_reviewed",
        ]
        widgets = {
            "contract_submitted_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
