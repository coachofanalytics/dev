from django import forms
from django.forms import Textarea
from accounts.models import Department
from .models import (
    Budget,
    Transaction,
    FinancialServiceRequest,
)

class InflowForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = "__all__"
        widgets = {"description": Textarea(attrs={"cols": 30, "rows": 1})}

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            "budget_lead", 
            "category", 
            "subcategory", 
            "item", 
            "qty", 
            "unit_price", 
            "description", 
            "is_active", 
            "receipt_link"
        ]
        widgets = {"description": Textarea(attrs={"cols": 30, "rows": 1})}

class DepartmentFilterForm(forms.Form):
    name = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label='Select a Deparment'
    ) 

class FinancialServiceRequestForm(forms.ModelForm):
    class Meta:
        model = FinancialServiceRequest
        fields = ['service_type', 'details']
        widgets = {
            'service_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-blue'}),
            'details': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-blue', 'rows': 4}),
        }
