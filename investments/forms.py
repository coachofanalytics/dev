from django import forms
from .models import InvestmentStrategy,Daily_Trades

class InvestmentStrategyForm(forms.ModelForm):
    class Meta:
        model = InvestmentStrategy
        fields = '__all__'
        widgets = {
            'symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AAPL'}),
            'action': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Iron Condor'}),
            'expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           
        }



class DailyTradesForm(forms.ModelForm):
    class Meta:
        model = Daily_Trades
        fields = "__all__"

    def clean_symbol(self):
        symbol = self.cleaned_data.get("symbol")
        if not symbol:
            raise forms.ValidationError("Symbol is required")
        return symbol
