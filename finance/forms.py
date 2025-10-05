from django import forms
from django.forms import Textarea
from django.db.models import Q
from pyexpat import model
from accounts.models import CustomerUser,Department
from datetime import datetime

from .models import (
    LoanApplication,
    Transaction,
    Inflow,
    FoodHistory,
    Budget,
    LoanProduct
)

# class DepartmentFilterForm(forms.Form):
#     name = forms.ModelChoiceField(
#         queryset=Department.objects.all(),
#         label='Select a Deparment'
#     )

class DepartmentFilterForm(forms.Form):
    def __init__(self, *args, departments=None, companies=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate department choices dynamically
        department_choices = [("", "All Departments")] + [
            (dept.name, dept.name) for dept in departments
        ] if departments else [("", "All Departments")]

        # Populate company choices dynamically
        company_choices = [(company.name, company.name) for company in companies] if companies else [("Coda", "Coda")]

        self.fields["name"] = forms.ChoiceField(
            choices=department_choices,
            required=False,
            label="Select Department"
        )

        self.fields["company"] = forms.ChoiceField(
            choices=company_choices,
            required=True,
            label="Select Company",
            initial="Coda"  # Default company selection
        )

    year = forms.IntegerField(
        required=True,
        label="Select Year",
        initial=datetime.now().year
    )

    month = forms.ChoiceField(
        required=False,
        choices=[('', 'All Months')] + [(str(i), str(i)) for i in range(1, 13)],
        label="Select Month (Optional)",
        initial=str(datetime.now().month)
    )

class FoodHistoryForm(forms.ModelForm):
    class Meta:
        model = FoodHistory
        fields = '__all__'

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction

        fields = [
            "id",
            "sender",
            "receiver",
            "vendor_supplier",
            "phone",
            "department",
            "category",
            "subcategory",
            "type",
            "payment_method",
            "qty",
            "amount",
            "transaction_cost",
            "description",
            "receipt_link",
        ]
        labels = {
            "sender": "Your full Name",
            "vendor_supplier": "Vendor/Supplier Name",
            "receiver": "Enter Receiver Name",
            "phone": "Receiver Phone",
            "department": "Department",
            "category": "category",
            "type": "Type",
            "payment_method": "Payment Method",
            "qty": "Quantity",
            "amount": "Unit Price",
            "transaction_cost": "Transaction Cost",
            "description": "Description",
            "receipt_link": "Link",
        }
        widgets = {"description": Textarea(attrs={"cols": 30, "rows": 1})}

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields["payment_method"].empty_label = "Select"


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget

        fields = [
            "company", 
            "budget_lead", 
            "department", 
            "category", 
            "subcategory", 
            "item", 
            "qty", 
            "unit_price", 
            "description", 
            "is_active", 
            "receipt_link"
        ]
        labels = {
            "company": "Company Name",
            "budget_lead": "Username",
            # "phone": "Receiver Phone",
            "department": "Department",
            "category": "Category",
            "subcategory": "Sub Category",
            "item": "Item",
            # "payment_method": "Payment Method",
            "qty": "Quantity",
            "unit_price": "Unit Price",
            # "transaction_cost": "Transaction Cost",
            "description": "Description",
            "receipt_link": "Link",
        }
        widgets = {"description": Textarea(attrs={"cols": 30, "rows": 1})}

    def __init__(self, *args, **kwargs):
        super(BudgetForm, self).__init__(*args, **kwargs)
        # self.fields["payment_method"].empty_label = "Select"


class InflowForm(forms.ModelForm):
    class Meta:
        model = Inflow
        fields = [
            "receiver",
            "sender",
            "phone",
            "country",
            "company",
            "category",
            "subcategory",
            "item",
            "method",
            "period",
            "qty",
            "amount",
            "transaction_cost",
            "description",
        ]
        labels = {
            "receiver": "Select Receiver",
            "phone": "Sender's Phone",
            "country": "Country",
            "company": "Company",
            "department": "Department",
            "category": "Category",
            "task": "Task",
            "item": "item",
            "method": "Payment Method",
            "period": "Period",
            "qty": "Quantity",
            "amount": "Unit Price",
            "transaction_cost": "Transaction Cost",
            "description": "Comments",
        }
        widgets = {"description": Textarea(attrs={"cols": 30, "rows": 1})}

    def __init__(self, *args, **kwargs):
        super(InflowForm, self).__init__(*args, **kwargs)
        self.fields["method"].empty_label = "Select"

class LoanForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        # fields = [ "user","category","amount","is_active"]
        fields = "__all__"
        
        # labels = {
        #     "user":"user",
        #     "category":"category",
        #     "amount":"amount",
        #     "is_active":"is_active",
        # }
    # def __init__(self, **kwargs):
    #     super(LoanForm, self).__init__(**kwargs)
    #     self.fields["user"].queryset = CustomerUser.objects.filter(
    #         Q(is_admin=True) | Q(is_staff=True)| Q(is_client=True)
    #     )


# ===== NEW OPTIMIZED LOAN FORMS =====

class LoanApplicationForm(forms.Form):
    """Form for loan application submission."""
    
    loan_amount = forms.DecimalField(
        label="Loan Amount",
        max_digits=10,
        decimal_places=2,
        min_value=100.00,
        max_value=100000.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter loan amount'
        })
    )
    
    loan_product = forms.ModelChoiceField(
        label="Loan Product",
        queryset=LoanProduct.objects.filter(is_active=True),
        empty_label="Select a loan product",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    purpose = forms.CharField(
        label="Purpose",
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe the purpose of this loan'
        })
    )
    
    employment_status = forms.ChoiceField(
        label="Employment Status",
        choices=[
            ('employed', 'Employed'),
            ('self_employed', 'Self-Employed'),
            ('unemployed', 'Unemployed'),
            ('student', 'Student'),
            ('retired', 'Retired')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    monthly_income = forms.DecimalField(
        label="Monthly Income",
        max_digits=10,
        decimal_places=2,
        min_value=0.00,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your monthly income'
        })
    )
    
    def clean_loan_amount(self):
        """Validate loan amount."""
        amount = self.cleaned_data.get('loan_amount')
        if amount and amount < 100.00:
            raise forms.ValidationError("Minimum loan amount is $100")
        return amount
    
    def clean_monthly_income(self):
        """Validate monthly income."""
        income = self.cleaned_data.get('monthly_income')
        if income and income < 0.00:
            raise forms.ValidationError("Monthly income cannot be negative")
        return income


class LoanApprovalForm(forms.Form):
    """Form for loan approval/rejection."""
    
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ]
    
    action = forms.ChoiceField(
        label="Action",
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    notes = forms.CharField(
        label="Notes",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about this decision'
        })
    )
    
    rejection_reason = forms.ChoiceField(
        label="Rejection Reason",
        required=False,
        choices=[
            ('insufficient_income', 'Insufficient Income'),
            ('poor_credit_history', 'Poor Credit History'),
            ('incomplete_documentation', 'Incomplete Documentation'),
            ('high_debt_ratio', 'High Debt-to-Income Ratio'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        """Validate form based on action selected."""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if action == 'reject' and not rejection_reason:
            raise forms.ValidationError("Rejection reason is required when rejecting an application")
        
        return cleaned_data