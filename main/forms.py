from django import forms
from django.db.models import Q
from django.forms import ModelForm, Textarea
from accounts.models import CustomerUser
from django import forms
from .models import WCAGStandardWebsite,Training
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

   


class WCAGStandardWebsiteForm(forms.ModelForm):
    class Meta:
        model = WCAGStandardWebsite
        fields = ["company", "app_name", "page_name", "website_url"]


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = '__all__'
