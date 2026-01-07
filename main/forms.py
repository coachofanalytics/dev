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
    # Add custom choices that match your HTML
    DOCUMENT_TYPE_CHOICES = [
        ('', 'Select a service'),
        ('Birth Certificate', 'Birth Certificate'),
        ('Marriage Certificate', 'Marriage Certificate'),
        ('Police Clearance (Good Conduct)', 'Police Clearance (Good Conduct)'),
        ('Legalization/Apostille (MFA)', 'Legalization/Apostille (MFA)'),
        ('Notarization/Oath Commissioner', 'Notarization/Oath Commissioner'),
        ('Other', 'Other / Custom Request'),
    ]
    
    PACKAGE_TYPE_CHOICES = [
        ('', 'Select a package (optional)'),
        ('standard', 'Standard ($99)'),
        ('premium', 'Premium ($249)'),
        ('diplomatic', 'Diplomatic ($399)'),
    ]
    
    # Override form fields to match your HTML
    documentType = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'id': 'documentType',
            'name': 'documentType',
            'required': 'required',
            'class': 'form-input bg-white',
        }),
        label="Type of Document Needed"
    )
    
    packageType = forms.ChoiceField(
        choices=PACKAGE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'id': 'packageType',
            'name': 'packageType',
            'class': 'form-input bg-white',
        }),
        label="Package Type (Optional)"
    )
    
    fullName = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'fullName',
            'name': 'fullName',
            'required': 'required',
            'class': 'form-input',
            'placeholder': 'John Doe',
        }),
        label="Full Name"
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'id': 'email',
            'name': 'email',
            'required': 'required',
            'class': 'form-input',
            'placeholder': 'you@example.com',
        }),
        label="Email Address"
    )
    
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'phone',
            'name': 'phone',
            'required': 'required',
            'class': 'form-input',
            'placeholder': '+254 7XX XXX XXX',
        }),
        label="Phone Number"
    )
    
    destinationCountry = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'destinationCountry',
            'name': 'destinationCountry',
            'required': 'required',
            'class': 'form-input',
            'placeholder': 'e.g., USA, Germany, UAE',
        }),
        label="Destination Country"
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'id': 'description',
            'name': 'description',
            'required': 'required',
            'class': 'form-input',
            'rows': '4',
            'placeholder': 'Explain what the document is needed for and any deadlines...',
        }),
        label="Brief Description of Need"
    )
    
    consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'id': 'consent',
            'name': 'consent',
            'required': 'required',
            'class': 'h-4 w-4 text-brand-blue border-gray-300 rounded focus:ring-brand-blue',
        }),
        label="I confirm the information provided is accurate."
    )
    
    class Meta:
        model = DocumentRequest
        fields = [
            'fullName', 'email', 'phone', 'documentType', 
            'packageType', 'destinationCountry', 'description', 'consent'
        ]
    
    def clean_consent(self):
        """Ensure consent is given"""
        consent = self.cleaned_data.get('consent')
        if not consent:
            raise forms.ValidationError("You must agree to the terms before submitting.")
        return consent