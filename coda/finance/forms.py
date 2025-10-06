from django import forms
from django.utils import timezone
from datetime import timedelta
from finance.models import BudgetRequest, Transaction, Inflow, FoodHistory, Budget

class BudgetRequestForm(forms.ModelForm):
    """Form for creating budget requests by regular users"""
    
    class Meta:
        model = BudgetRequest
        fields = [
            'amount', 'currency', 'purpose', 'department', 'budget_category',
            'required_date', 'priority', 'cost_center', 'attachments'
        ]
        widgets = {
            'purpose': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Describe the purpose and justification for this budget request...'
            }),
            'required_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': 'today'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PROJ-2024-Q1, MKT-CAMPAIGN-001'
            }),
            'attachments': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'List any supporting documents (comma-separated)'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default currency
        self.fields['currency'].initial = 'USD'
        
        # Set default priority
        self.fields['priority'].initial = 'medium'
        
        # Set default required date to 30 days from now
        if not self.instance.pk:
            self.fields['required_date'].initial = timezone.now().date() + timedelta(days=30)
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name != 'attachments':
                field.widget.attrs['class'] = 'form-control'
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
    
    def clean_required_date(self):
        required_date = self.cleaned_data.get('required_date')
        if required_date and required_date < timezone.now().date():
            raise forms.ValidationError('Required date cannot be in the past.')
        return required_date
    
    def clean_cost_center(self):
        cost_center = self.cleaned_data.get('cost_center')
        if cost_center:
            # Basic validation for cost center format
            if len(cost_center) < 3:
                raise forms.ValidationError('Cost center must be at least 3 characters long.')
        return cost_center
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.requester = self.user
            instance.created_by = self.user
            instance.last_modified_by = self.user
        if commit:
            instance.save()
        return instance


# Existing forms that were in the original file
class TransactionForm(forms.ModelForm):
    """Form for transaction entries"""
    class Meta:
        model = Transaction
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class InflowForm(forms.ModelForm):
    """Form for inflow entries"""
    class Meta:
        model = Inflow
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DepartmentFilterForm(forms.Form):
    """Form for filtering by department"""
    def __init__(self, *args, departments=None, companies=None, **kwargs):
        super().__init__(*args, **kwargs)
        if departments:
            self.fields['name'] = forms.ModelChoiceField(
                queryset=departments,
                empty_label="All Departments",
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        else:
            self.fields['name'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department name'})
            )


class FoodHistoryForm(forms.ModelForm):
    """Form for food history entries"""
    class Meta:
        model = FoodHistory
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class BudgetForm(forms.ModelForm):
    """Form for budget entries"""
    class Meta:
        model = Budget
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }