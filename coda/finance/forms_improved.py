"""
Improved Transaction Form with intelligent auto-suggestions
Based on learnings from transaction data analysis (October 2025)

Key Improvements:
1. Category is REQUIRED (prevent 79.8% uncategorized issue)
2. Auto-suggest category based on receiver, department, amount
3. Validate against location data in receiver field
4. Standardized receiver names via lookup
5. Real-time validation and warnings
"""

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Avg
from finance.models import Transaction, BudgetCategory
from accounts.models import Department
from decimal import Decimal
import re


class SmartTransactionForm(forms.ModelForm):
    """
    Intelligent transaction form with auto-suggestions and validation
    
    Features:
    - Required category field
    - Auto-complete receiver names
    - Category auto-suggestion
    - Amount validation
    - Location field separation
    """
    
    # Add location field (will be added to model later)
    location = forms.ChoiceField(
        choices=[
            ('', '-- Select Location (if applicable) --'),
            ('matunda', 'Matunda Office'),
            ('makutano', 'Makutano Office'),
            ('nairobi_hq', 'Nairobi HQ'),
            ('remote', 'Remote/External'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_location'
        }),
        help_text="Select CODA office location if this is an internal transfer"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'sender', 'vendor_supplier', 'receiver', 'phone',
            'department', 'category', 'subcategory', 'type',
            'transaction_date', 'qty', 'amount', 'currency',
            'transaction_cost', 'description', 'payment_method',
            'receipt_link'
        ]
        
        widgets = {
            'receiver': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_receiver',
                'placeholder': 'Enter receiver name...',
                'autocomplete': 'off',
                'data-provide': 'typeahead',  # Bootstrap typeahead
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category',
                'required': 'required',  # Make it visually required
            }),
            'department': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_department',
                'required': 'required',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_amount',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_description',
                'rows': 3,
                'placeholder': 'Provide detailed description (minimum 10 characters)...',
                'required': 'required',
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_currency',
            }),
            'qty': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transaction_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'receipt_link': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make category required
        self.fields['category'].required = True
        self.fields['category'].empty_label = "-- Select Category (Required) --"
        
        # Make department required
        self.fields['department'].required = True
        
        # Make description required with minimum length
        self.fields['description'].required = True
        
        # Set currency default and enable
        self.fields['currency'].initial = 'USD'
        self.fields['currency'].required = False
        self.fields['currency'].disabled = False
        
        # Add help text based on learnings
        self.fields['receiver'].help_text = (
            "Enter recipient name. Start typing for suggestions. "
            "Do NOT enter location names here (use Location field)."
        )
        
        self.fields['category'].help_text = (
            "Will auto-suggest based on receiver and amount. "
            "This field is REQUIRED."
        )
        
        self.fields['amount'].help_text = (
            "Will show warning if amount is unusual for selected category."
        )
    
    def clean_receiver(self):
        """Validate receiver field"""
        receiver = self.cleaned_data.get('receiver', '')
        
        if not receiver:
            raise ValidationError("Receiver name is required")
        
        # Check for location keywords that shouldn't be in receiver
        location_keywords = ['matunda', 'makutano', 'office', 'coda hq']
        receiver_lower = receiver.lower()
        
        for keyword in location_keywords:
            if keyword in receiver_lower:
                raise ValidationError(
                    f"'{receiver}' looks like a location. "
                    f"Please use the 'Location' field for office locations "
                    f"and enter the actual person's name in 'Receiver'."
                )
        
        # Standardize capitalization (Title Case)
        receiver = receiver.title()
        
        return receiver
    
    def clean_category(self):
        """Ensure category is selected"""
        category = self.cleaned_data.get('category')
        
        if not category:
            raise ValidationError(
                "Category is required. This helps us track spending accurately."
            )
        
        return category
    
    def clean_description(self):
        """Validate description has meaningful content"""
        description = self.cleaned_data.get('description', '')
        
        if len(description.strip()) < 10:
            raise ValidationError(
                "Description must be at least 10 characters. "
                "Please provide detailed information about this transaction."
            )
        
        return description
    
    def clean(self):
        """Cross-field validation and amount checking"""
        cleaned_data = super().clean()
        
        amount = cleaned_data.get('amount')
        category = cleaned_data.get('category')
        department = cleaned_data.get('department')
        
        # Validate amount is positive
        if amount and amount <= 0:
            self.add_error('amount', "Amount must be greater than zero")
        
        # Check if amount is unusual for this category
        if amount and category:
            # Get average amount for this category
            avg_amount = Transaction.objects.filter(
                category=category
            ).aggregate(avg=Avg('amount'))['avg']
            
            if avg_amount:
                # If amount is more than 3x the average, add warning
                if amount > avg_amount * 3:
                    # This is a warning, not an error - allow but flag
                    # In the template, we'll show this as a warning message
                    self.add_warning = True
                    self.warning_message = (
                        f"This amount (${amount:,.2f}) is unusually high for "
                        f"{category.name}. Average is ${avg_amount:,.2f}. "
                        f"Please verify this is correct."
                    )
        
        # Flag large transactions (>$10,000) for review
        if amount and amount > 10000:
            cleaned_data['requires_approval'] = True
        
        return cleaned_data
    
    def get_category_suggestion(self):
        """
        Suggest category based on receiver, department, and amount
        
        Based on patterns learned from data analysis:
        - Amount range is most predictive (239 matches)
        - Department context adds value (178 matches)
        - Receiver name helps (100 matches)
        """
        receiver = self.cleaned_data.get('receiver', '').lower()
        department = self.cleaned_data.get('department')
        amount = self.cleaned_data.get('amount')
        
        suggestions = []
        
        # Pattern 1: Known vendors (high confidence)
        vendor_categories = {
            'kplc': 'Utilities',
            'safaricom': 'IT and Software',
            'kenya power': 'Utilities',
            'nairobi water': 'Utilities',
        }
        
        for vendor, category in vendor_categories.items():
            if vendor in receiver:
                try:
                    cat = BudgetCategory.objects.get(name=category)
                    return {'category': cat, 'confidence': 'high', 'reason': f'Known vendor: {vendor}'}
                except BudgetCategory.DoesNotExist:
                    pass
        
        # Pattern 2: HR Department + Amount Range (high confidence)
        if department and department.name == 'HR Department':
            if amount and 1000 <= amount <= 50000:
                try:
                    cat = BudgetCategory.objects.get(name='Salaries and Wages')
                    return {'category': cat, 'confidence': 'high', 'reason': 'HR Department + Salary range'}
                except BudgetCategory.DoesNotExist:
                    pass
            elif amount and 500 <= amount <= 10000:
                try:
                    cat = BudgetCategory.objects.get(name='Human Resources')
                    return {'category': cat, 'confidence': 'medium', 'reason': 'HR Department + HR range'}
                except BudgetCategory.DoesNotExist:
                    pass
        
        # Pattern 3: Amount-based suggestions
        if amount:
            if 100 <= amount <= 2000:
                # Likely travel or small operational
                suggestions.append({'name': 'Travel and Entertainment', 'confidence': 'low'})
                suggestions.append({'name': 'Operational Expenses', 'confidence': 'low'})
            elif 500 <= amount <= 10000:
                # Could be utilities, operations, or HR
                suggestions.append({'name': 'Utilities', 'confidence': 'low'})
                suggestions.append({'name': 'Operational Expenses', 'confidence': 'low'})
        
        # Return first suggestion if any
        if suggestions:
            try:
                cat = BudgetCategory.objects.get(name=suggestions[0]['name'])
                return {'category': cat, 'confidence': suggestions[0]['confidence'], 'reason': 'Amount range'}
            except BudgetCategory.DoesNotExist:
                pass
        
        return None


class TransactionBulkUploadForm(forms.Form):
    """
    Bulk upload transactions from CSV
    Useful for importing bank statements
    """
    
    csv_file = forms.FileField(
        label="Upload CSV File",
        help_text="CSV should have columns: date, receiver, amount, description",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx'
        })
    )
    
    default_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        help_text="Default department for all transactions in this upload"
    )
    
    auto_categorize = forms.BooleanField(
        initial=True,
        required=False,
        label="Auto-categorize transactions",
        help_text="Attempt to automatically assign categories based on patterns"
    )


