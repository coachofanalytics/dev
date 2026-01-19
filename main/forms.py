from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Textarea
from django.contrib.auth.forms import UserCreationForm
# from accounts.models import CustomerUser, 
from .models import Feedback, Donation_organisation, ContactMessage,Scholarship
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

class DonorForm(forms.ModelForm):
    class Meta:
        model = Donation_organisation
        fields = ("donor_name", "email", "amount", "message")

class MessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "message")

# scholarship Form

class ScholarshipSearchForm(forms.Form):
    search_keyword = forms.CharField(
        required= False,
        widget =forms.TextInput(attrs={
            'placeholder':'e.g., STEM, Business, PhP',
            'class':'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue'
        })
    )
    filter_level = forms.ChoiceField(
        required= False,
        choices=[('All', 'All Level')] + Scholarship.LEVEL_CHOICES,
        widget =forms.Select(attrs={
            'class':'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue bg-white'
        })
    )
    filter_field = forms.ChoiceField(
        required= False,
        choices=[('All', 'All Fields')] + Scholarship.FIELDS_CHOICES,
        widget =forms.Select(attrs={
            'class':'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue bg-white'
        })
    )
    filter_location = forms.ChoiceField(
        required= False,
        choices=[('All', 'Any Location')] + Scholarship.LOCATION_CHOICES,
        widget =forms.Select(attrs={
            'class':'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue bg-white'
        })
    )
    filter_status = forms.BooleanField(
        required = False,
        label = 'show only "Closing Soon"',
        widget = forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-brand-red border-gray-300 rounded focus:ring-brand-red'
        })
    )
    


from .models import Governance

class GovernanceForm(forms.ModelForm):
    class Meta:
        model = Governance
        fields = ['governance_category', 'description', 'members']

