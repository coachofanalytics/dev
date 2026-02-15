from django import forms
from django.db.models import Q
from accounts.models import CustomerUser
# from .models import Expenses
from .models import *
# from django.db import transactionfrom django import forms
from main.models import Location

class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomerUser.objects.filter(Q(is_client=True) | Q(is_staff=True)),
        label='Select a client'

    )

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["country", "state", "city", "zipcode"]

        from django import forms
from .models import Testimonials

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonials
        fields = ['title', 'content', 'writer']
