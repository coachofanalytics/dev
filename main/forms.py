from django import forms
from django.db.models import Q
from django.forms import ModelForm, Textarea
from accounts.models import CustomerUser
from django.utils.translation import gettext_lazy as _
# from .models import Expenses
from .models import *
# from django.db import transaction
from multiupload.fields import MultiFileField

class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomerUser.objects.filter(Q(is_client=True) | Q(is_staff=True)),
        label='Select a client'
    )
class locationForm(forms.Form):
    class Meta:
        model = Location
        fields = ['zipcode','city','state','county']
