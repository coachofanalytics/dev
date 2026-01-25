from django import forms
from django.db.models import Q
from django.forms import ModelForm, Textarea
from accounts.models import CustomerUser
from django.utils.translation import gettext_lazy as _
# from .models import Expenses
from .models import *
# from django.db import transaction
from multiupload.fields import MultiFileField
from django import forms
from .models import ServiceCategory

class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomerUser.objects.filter(Q(is_client=True) | Q(is_staff=True)),
        label='Select a client'
    )
from django import forms
from .models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['zipcode', 'city', 'state', 'country']



class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ["service", "name", "slug", "description", "is_active", "is_featured"]
