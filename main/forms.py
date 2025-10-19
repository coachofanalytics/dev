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

class volunteersform(forms.ModelForm):
    class Meta:
        model = Volunteer
        fields = ['company_name','email','motivation','image']        



class TestimonialForm(forms.ModelForm):
    class Meta:
        model =Testimonials
        fields = ['title', 'slug', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
