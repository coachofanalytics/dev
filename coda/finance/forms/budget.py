"""
Budget forms for editing and approval workflows.
"""

from django import forms
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging

from ..models import Budget, BudgetCategory, BudgetSubCategory, BudgetRequest, ApprovalPolicy

logger = logging.getLogger(__name__)
User = get_user_model()


class BudgetEditForm(forms.ModelForm):
    """Form for editing budget items."""
    
    class Meta:
        model = Budget
        fields = [
            'item_name', 'description', 'estimated_amount', 
            'quantity', 'unit_price', 'cases', 'start_date', 
            'end_date', 'notes'
        ]
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter budget item name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'estimated_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'cases': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }
    
    def clean_estimated_amount(self):
        """Validate estimated amount."""
        amount = self.cleaned_data.get('estimated_amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Estimated amount must be positive.")
        return amount
    
    def clean_quantity(self):
        """Validate quantity."""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError("Quantity must be positive.")
        return quantity
    
    def clean_unit_price(self):
        """Validate unit price."""
        price = self.cleaned_data.get('unit_price')
        if price and price <= 0:
            raise forms.ValidationError("Unit price must be positive.")
        return price
    
    def clean_cases(self):
        """Validate cases."""
        cases = self.cleaned_data.get('cases')
        if cases and cases <= 0:
            raise forms.ValidationError("Cases must be positive.")
        return cases
    
    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data


class BudgetRequestForm(forms.ModelForm):
    """Form for creating budget requests."""
    
    # Override currency as ChoiceField to ensure it's editable
    currency = forms.ChoiceField(
        choices=[
            ('KES', 'KES - Kenyan Shilling'),
            ('USD', 'USD - US Dollar'),
            ('EUR', 'EUR - Euro'),
            ('GBP', 'GBP - British Pound'),
        ],
        initial='KES',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_currency'
        })
    )
    
    # Override priority as ChoiceField
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_priority'
        })
    )
    
    class Meta:
        model = BudgetRequest
        fields = [
            'amount', 'currency', 'purpose', 'department', 'budget_category',
            'required_date', 'priority', 'cost_center', 'attachments'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter requested amount'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the purpose of the budget request'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_department'
            }),
            'budget_category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_budget_category'
            }),
            'required_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PROJ-2024-Q1'
            }),
            'attachments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List supporting documents (comma-separated)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def clean_attachments(self):
        """Convert comma-separated string to JSON list."""
        attachments = self.cleaned_data.get('attachments', '')
        
        # Handle different input types
        if isinstance(attachments, list):
            # Already a list, just clean it
            return [doc.strip() for doc in attachments if doc and doc.strip()]
        elif isinstance(attachments, str):
            # String input, split by comma
            if attachments:
                attachment_list = [doc.strip() for doc in attachments.split(',') if doc.strip()]
                return attachment_list
        elif attachments is None:
            return []
        
        return []
    
    def clean_requested_amount(self):
        """Validate requested amount."""
        amount = self.cleaned_data.get('requested_amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Requested amount must be positive.")
        return amount
    
    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        
        if category and subcategory and subcategory.category != category:
            raise forms.ValidationError("Subcategory must belong to the selected category.")
        
        return cleaned_data


class BudgetApprovalForm(forms.Form):
    """Form for approving or rejecting budget requests."""
    
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add comments (optional)'
        })
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rejection (required if rejecting)'
        })
    )
    
    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if action == 'reject' and not rejection_reason:
            raise forms.ValidationError("Rejection reason is required when rejecting a request.")
        
        return cleaned_data


class BudgetComparisonForm(forms.Form):
    """Form for budget comparison parameters."""
    
    COMPARISON_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    comparison_type = forms.ChoiceField(
        choices=COMPARISON_TYPE_CHOICES,
        initial='monthly',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    periods = forms.IntegerField(
        initial=6,
        min_value=1,
        max_value=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '24'
        })
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company and hasattr(company, 'departments'):
            self.fields['department'].queryset = company.departments.all()


class BudgetSearchForm(forms.Form):
    """Form for searching budgets."""
    
    SEARCH_FIELDS = [
        ('item_name', 'Item Name'),
        ('description', 'Description'),
        ('category', 'Category'),
        ('subcategory', 'Subcategory'),
    ]
    
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        initial='item_name',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term'
        })
    )
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('Draft', 'Draft'),
            ('Submitted', 'Submitted'),
            ('Approved', 'Approved'),
            ('Active', 'Active'),
            ('Completed', 'Completed'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def clean_search_query(self):
        """Validate search query."""
        query = self.cleaned_data.get('search_query')
        if query and len(query.strip()) < 2:
            raise forms.ValidationError("Search query must be at least 2 characters long.")
        return query
