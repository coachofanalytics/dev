from django import forms
from .models import Testimonial, Feedback, Donation_organisation, Donation_organization, ContactMessage, Scholarship
from django.utils import timezone
from .models import AppointmentRequest
# Feedback / Contact Form

from django.contrib.auth.models import User
from .models import (
    Feedback, Donation_organisation, Donation_organization, 
    ContactMessage, Scholarship, Governance  # ← Add Governance here
)

class GovernanceForm(forms.ModelForm):
    """
    Form for creating and updating Governance records
    """
    # Add these fields for new user creation
    new_username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'New username'
        }),
        label="Create New User (Username)"
    )
    
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        }),
        label="Password for new user"
    )
    
    new_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email (optional)'
        }),
        label="Email for new user"
    )
    
    class Meta:
        model = Governance
        fields = ['governance_category', 'description', 'members']
        widgets = {
            'governance_category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter governance category'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter detailed description'
            }),
            'members': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make members field not required (we'll validate in clean)
        self.fields['members'].required = False
        self.fields['members'].label = "Select Existing Member"
        
        # Make members field show usernames nicely
        self.fields['members'].label_from_instance = lambda obj: f"{obj.username} ({obj.email})"
    
    def clean(self):
        cleaned_data = super().clean()
        members = cleaned_data.get('members')
        new_username = cleaned_data.get('new_username', '').strip()
        new_password = cleaned_data.get('new_password', '').strip()
        
        print(f"DEBUG - Form clean: members={members}, new_username={new_username}")
        
        # Validate: Either select existing member OR create new one
        if not members and not new_username:
            raise forms.ValidationError(
                "You must either select an existing member or create a new one."
            )
        
        # If creating new user, password is required
        if new_username and not new_password:
            raise forms.ValidationError({
                'new_password': "Password is required when creating a new user."
            })
        
        # If new username provided but also selected existing member
        if new_username and members:
            raise forms.ValidationError(
                "Please choose only one option: either select an existing member OR create a new one."
            )
        
        return cleaned_data


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
    search_keyword = forms.CharField(required=False,
    widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 '
        'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
        'placeholder': 'Search By title, provider...'
    })
    )

    filter_level = forms.ChoiceField(required=False, 
                   choices=[('', 'All Levels')] + Scholarship.Level.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    
    filter_field = forms.ChoiceField(required=False, 
                   choices=[('', 'All Fields')] + Scholarship.Field.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    filter_location = forms.ChoiceField(required=False, 
                   choices=[('', 'All Locations')] + Scholarship.Location.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    filter_currency = forms.ChoiceField(required=False, 
                   choices=[('', 'All Currencies')] + Scholarship.Currency.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    filter_status = forms.BooleanField(required=False, 
                   label="Show only Closing Soon",
                   widget=forms.CheckboxInput(attrs={
                       'class': 'h-4 w-4 text-brand-blue focus:ring-brand-blue border-gray-300 rounded'
                   })
                   )
    
    
    
    
    


from .models import Governance

class GovernanceForm(forms.ModelForm):
    class Meta:
        model = Governance
        fields = ['governance_category', 'description', 'members']






class SearchForm(forms.Form):
    specialty = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Specialty (e.g., Cardiologist, Dentist)',
        'class': 'search-input',
        'id': 'specialty-input',
    }))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Location (City or Country)',
        'class': 'search-input',
        'id': 'location-input',
    }))


class AppointmentRequestForm(forms.ModelForm):
    class Meta:
        model = AppointmentRequest
        fields = ['full_name', 'email', 'preferred_date', 'preferred_time', 'reason', 'honeypot']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
                'required': True,
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'preferred_time': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Briefly describe your reason for the appointment...',
                'required': True,
            }),
            'honeypot': forms.HiddenInput(),
        }

    def clean_honeypot(self):
        value = self.cleaned_data.get('honeypot', '')
        if value:
            raise forms.ValidationError('Spam detected.')
        return value

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError('Please select a future date.')
        return date
    



