from django import forms
from .models import investment_content


class InvestmentContentForm(forms.ModelForm):
    class Meta:
        model = investment_content
        fields = ["title", "slug", "description"]
