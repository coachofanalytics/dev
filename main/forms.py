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
from django import forms
from .models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['zipcode', 'city', 'state', 'country']

        from django import forms
from .models import ClientAvailability

class ClientAvailabilityForm(forms.ModelForm):
    class Meta:
        model = ClientAvailability
        fields = ['client', 'day', 'start_time', 'end_time', 'time_standards', 'topic', 'recurring_weekly']

from django import forms
from .models import ClientAvailability

class ClientAvailabilityForm(forms.ModelForm):
    class Meta:
        model = ClientAvailability
        fields = ['client', 'day', 'start_time', 'end_time', 'topic', 'recurring_weekly']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'topic': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.TextInput(attrs={'class': 'form-control'}),
            'recurring_weekly': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
