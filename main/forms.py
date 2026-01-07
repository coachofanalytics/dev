from django import forms
from django.forms import ModelForm
from .models import Feedback, Donation_organisation, Donation_organization, ContactMessage, Scholarship, DocumentRequest

# Feedback / Contact Form
class ContactForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            "user",
            "topic",
            "description",
        ]
        labels = {
            "user": "Staff/Employee",
            "topic": "Type your topic",
            "description": "Describe your issue or question in detail",
        }

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['user'].required = False
        self.fields['topic'].required = False


# Donation Organization Forms
class DonationOrganizationForm(forms.ModelForm):
    class Meta:
        model = Donation_organization
        fields = ['donor_name', 'email', 'amount', 'message']

# DonorForm for the organization spelled with underscore
class DonorForm(forms.ModelForm):
    class Meta:
        model = Donation_organisation
        fields = ['donor_name', 'email', 'amount', 'message']

# Contact Message Form
class MessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']


# Scholarship Search Form
class ScholarshipSearchForm(forms.Form):
    search_keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'e.g., STEM, Business, PhP',
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue'
            }
        )
    )

    filter_level = forms.ChoiceField(
        required=False,
        choices=[('', 'All Levels')] + Scholarship.LEVEL_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue bg-white'
            }
        )
    )

    filter_field = forms.ChoiceField(
        required=False,
        choices=[('', 'All Fields')] + Scholarship.FIELD_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue bg-white'
            }
        )
    )

    filter_location = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Location')] + Scholarship.LOCATION_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg focus:ring-brand-blue focus:border-brand-blue bg-white'
            }
        )
    )

    filter_status = forms.BooleanField(
        required=False,
        label='Show only "Closing Soon"',
        widget=forms.CheckboxInput(
            attrs={
                'class': 'h-4 w-4 text-brand-red border-gray-300 rounded focus:ring-brand-red'
            }
        )
    )

class DocumentRequestForm(forms.ModelForm):
    class Meta:
        model = DocumentRequest
        fields = ['full_name', 'email', 'phone', 'document_type', 'package_type', 'destination_country', 'description', 'consent']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input','placeholder':'John Doe'}),
            'email': forms.EmailInput(attrs={'class': 'form-input','placeholder':'john@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input','placeholder':'+255 12345678'}),
            'document_type': forms.Select(attrs={'class': 'form-input bg-white'}),
            'package_type': forms.Select(attrs={'class': 'form-input bg-white'}),
            'destination_country': forms.TextInput(attrs={'class': 'form-input','placeholder':'e.g., Kenya,Rwanda,USA'}),
            'description': forms.Textarea(attrs={'class': 'form-input','rows':4,'placeholder':'Description'}),
            'consent': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-brand-blue border-gray-300 rounded focus:ring-brand-blue'}),
        }