from django import forms
from django.db.models import Q
from accounts.models import CustomerUser
# from .models import Expenses
from .models import *
# from django.db import transaction

class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomerUser.objects.filter(Q(is_client=True) | Q(is_staff=True)),
        label='Select a client'
    )
