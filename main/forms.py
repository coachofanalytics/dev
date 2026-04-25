from django import forms
from django.forms import ModelForm
from .models import Feedback, Donation_organisation, Donation_organization, ContactMessage, Scholarship

from .models import Consultation
from .models import NetworkItem

#new code i create myself

from .models import NetworkItem

# forms.py

from .models import Application
from .models import Donation

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['motivation']
class NetworkItemForm(forms.ModelForm):
    class Meta:
        model = NetworkItem
        fields = ['title', 'description', 'category', 'urgency', 'location']
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

#added myself



class ConsultationForm(forms.ModelForm):

    class Meta:
        model = Consultation

        fields = [
            'full_name',
            'email',
            'phone',
            'country',
            'consultation_type',
            'description',
            'document',
            'preferred_date'
        ]

        
#new form for donation

class DonationForm(forms.ModelForm):
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Enter amount"})
    )

    class Meta:
        model = Donation
        fields = ["name", "email", "amount", "message", "anonymous"]

from .models import Volunteer, SupportTicket


class VolunteerForm(forms.ModelForm):
    class Meta:
        model = Volunteer

        # ONLY fields the volunteer should fill
        fields = [
            'full_name',
            'email',
            'phone',
            'gender',
            'date_of_birth',
            'country',
            'city',
            'profile_photo',

            'availability',
            'available_days',
            'hours_per_week',

            'skills',
            'interests',

            'territory',
            'is_remote',

            'motivation',
            'experience',
            'impact_goal',

            'cv',
            'id_document',
            'certificates',

            'role',

            'emergency_name',
            'emergency_relationship',
            'emergency_phone',

            'accepted_terms',
            'receive_updates',
        ]

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type':'date'}),
            'motivation': forms.Textarea(attrs={'rows':3}),
            'experience': forms.Textarea(attrs={'rows':3}),
            'impact_goal': forms.Textarea(attrs={'rows':3}),
            'skills': forms.Textarea(attrs={'rows':2}),
            'interests': forms.Textarea(attrs={'rows':2}),
        }
   

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket

        # fields user can fill ONLY
        fields = [
            'full_name','email','phone','user_type',
            'category','priority','subject','message','attachment'
        ]

        widgets = {
            'message': forms.Textarea(attrs={'rows':4}),
        }