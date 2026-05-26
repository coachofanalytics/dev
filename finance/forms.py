from django import forms
from django.forms import Textarea
from accounts.models import Department

from .models import (
    Budget,
    Transaction,
    Opportunity,
)


class InflowForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = "__all__"
        # fields = [
        #     "receiver",
        #     "phone",
        #     "category",
        #     "task",
        #     "method",
        #     "period",
        #     "qty",
        #     "amount",
        #     "transaction_cost",
        #     "description",
        # ]
        labels = {
            "receiver": "Enter Receiver Name",
            "phone": "Receiver Phone",
            "sender_phone": "Sender's Number",
            "department": "Department",
            "category": "Category",
            "task": "Task",
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
            "receipt_link",
        ]
        labels = {
            "company": "Company Name",
            "budget_lead": "Username",
            # "phone": "Receiver Phone",
            "subcategory": "subcategory",
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


class DepartmentFilterForm(forms.Form):
    name = forms.ModelChoiceField(
        queryset=Department.objects.all(), label="Select a Deparment"
    )


class PaymentForm(forms.Form):
    # model = Payment
    amount = forms.DecimalField(
        label="", max_digits=10, decimal_places=2, required=True
    )
    currency = forms.ChoiceField(
        choices=[("USD", "USD"), ("EUR", "EUR"), ("KES", "KES")],
        label="",
        required=True,
    )
    email = forms.EmailField(label="", required=True)
    first_name = forms.CharField(label="", max_length=30, required=True)
    last_name = forms.CharField(label="", max_length=30, required=True)
    payment_purpose = forms.CharField(label="", max_length=100, required=True)
    phone = forms.CharField(label="", max_length=17, required=False)


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            'title',
            'type',
            'contact',
            'description'
        ]
