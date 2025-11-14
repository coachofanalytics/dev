from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Textarea
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomerUser
from .models import Feedback
from django.utils.translation import gettext_lazy as _

class ContactForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            "user",
            # "category",
            # "sub_category",
            "topic",
            "description",
        ]
        labels = {
            "user": "Staff/Employee",
            # "category": "Pick your Category</h2>",
            # "subcategory": "Are You a Client/Staff?(Select Other if None of the above)",
            "topic": "Type your topic",
            "description": "Describe your issue or question in detail",
        }

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['user'].required=False
        self.fields['topic'].required=False


# Form for editing Donation_organization
from .models import Donation_organization
class DonationOrganizationForm(forms.ModelForm):
    class Meta:
        model = Donation_organization
        fields = ['donor_name', 'email', 'amount', 'message']


# Simple search form for scholarships used by the scholarship_search view/template
class ScholarshipSearchForm(forms.Form):
    search_keyword = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={'id': 'search-keyword', 'placeholder': 'Search by title or provider'}))
    FILTER_CHOICES = [('', 'All'), ('Undergraduate', 'Undergraduate'), ('Postgraduate', 'Postgraduate'), ('Doctorate', 'Doctorate')]
    filter_level = forms.ChoiceField(choices=FILTER_CHOICES, required=False)
    filter_field = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={'placeholder': 'e.g. STEM, Business'}))
    filter_location = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={'placeholder': 'Country or region'}))
    filter_status = forms.BooleanField(required=False, label='Closing soon only')




        
        




