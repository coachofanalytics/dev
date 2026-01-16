from django import forms
from django.forms import ModelForm
from .models import Feedback, Donation_organisation, Donation_organization, ContactMessage, Scholarship, DocumentationRequest

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

class DocumentationRequestForm(forms.ModelForm):
    DOCUMENT_TYPE_CHOICES = [
        ('','Select Service'),
        ('birth', 'Birth Certificate'),
        ('marriage', 'Marriage Certificate'),
        ('police_clearance', 'Police Clearance (Good Conduct)'),
        ('legalization', 'Legalization/Apostille (MFA)'),
        ('notarization', 'Notarization/Oath Commissioner'),
        ('other', 'Other/Custom'),
    ]
    PACKAGE_TYPE_CHOICES = [
        ('','Select Package(Optional)'),
        ('standard', 'Standard ($99)'),
        ('premium', 'Premium ($249)'),
        ('diplomatic', 'Diplomatic ($399)'),
    ]
    document_type = forms.ChoiceField(choices=DOCUMENT_TYPE_CHOICES,
    widget=forms.Select(
        attrs={
            'id': 'document_type',
            'class': 'form-input bg-white'
        }
    ), label="type of document needed")
    package_type = forms.ChoiceField(choices=PACKAGE_TYPE_CHOICES,
    required=False,
    widget=forms.Select(
        attrs={
            'id': 'package_type',
            'class': 'form-input bg-white'
        }
    ), label="package type (optional)")
    full_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'full_name',
                'class': 'form-input bg-white',
                'placeholder': 'John Doe',
            }
        ), label="full name")
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'id': 'email',
                'class': 'form-input bg-white',
                'placeholder': 'you@example.com',
            }
        ), label="Email Address")
    phone= forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'id_phone',
                'class': 'form-input bg-white',
                'placeholder': '+254 7XX XXX XXX',
            }
        ), label="Phone Number")
    destination_country = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'destination_country',
                'class': 'form-input bg-white',
                'placeholder': 'e.g., USA, Germany, UAE',
            }
        ), label="Destination Country")
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'id': 'description',
                'class': 'form-input bg-white',
                'rows': 4,
                'placeholder': 'Explain what the document is needed for and any deadlines...',
            }
        ), label="Brief Description of Need")
    consent = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'id': 'consent',
                'class': 'form-input bg-white',
            }
        ), label="I consent to the processing of my personal data for the purpose of providing the service")
    class Meta:
        model = DocumentationRequest
        fields = ['full_name', 'email', 'phone', 'document_type', 'package_type', 'destination_country','description', 'consent']
    def clean_consent(self):
        consent = self.cleaned_data.get('consent')
        if not consent:
            raise forms.ValidationError("You must consent to the processing of your personal data for the purpose of providing the service")
        return consent