from django import forms
from .models import OverBoughtSold

class OverBoughtSoldForm(forms.ModelForm):
    class Meta:
        model = OverBoughtSold
        fields = [
            "symbol", "description", "last", "volume", "RSI",
            "EPS", "PE", "rank", "profit_margins"
        ]
