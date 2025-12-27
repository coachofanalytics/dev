from django import forms
from django.forms import Textarea
from django.db.models import Q
from pyexpat import model
from accounts.models import Department

from .models import (
    Budget,
    Transaction,
   
)



class InflowForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields= "__all__"
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
            "receipt_link"
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
        queryset=Department.objects.all(),
        label='Select a Deparment'
    ) 