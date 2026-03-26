from django import forms
from .models import Testimonial, Feedback, Donation_organisation, Donation_organization, ContactMessage, Scholarship
from django.utils import timezone
from .models import AppointmentRequest
# Feedback / Contact Form

from django.contrib.auth.models import User
from .models import (
    Feedback, Donation_organisation, Donation_organization, 
    ContactMessage, Scholarship, Governance,  # ← Add Governance here
    # Communities models
    CommunityMember, DirectoryProfile, ForumCategory, Post, CommentP, EventCalendar,
    # Memberjoin models
    MembershipRegistration
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







# ============================================
# COMMUNITIES APP FORMS
# ============================================


class CommunitiesJoinForm(forms.ModelForm):
    """Form for basic community membership"""
    agree_to_directory = forms.BooleanField(
        required=False,
        label='I want to appear in the public member directory'
    )
    email_updates = forms.BooleanField(
        required=False,
        label='I would like to receive email updates'
    )
    agree_terms = forms.BooleanField(
        required=True,
        label='I agree to the community terms and conditions'
    )
    
    class Meta:
        model = CommunityMember
        fields = ['name', 'email', 'phone', 'profession', 'region', 'specialization', 'bio', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'profession': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Profession'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Region/Country'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area of Specialization'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Website URL (optional)'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CommunityMember.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class CommunitiesDirectoryProfileForm(forms.ModelForm):
    """Form for detailed member directory profile"""
    
    class Meta:
        model = DirectoryProfile
        fields = ['full_name', 'profession', 'region_city', 'category', 'membership_type', 'expertise_summary', 'profile_photo']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'region_city': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
            'expertise_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CommunitiesPostForm(forms.ModelForm):
    """Form for creating forum posts"""
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Post Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Post Content'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }


class CommunitiesCommentForm(forms.ModelForm):
    """Form for posting comments on forum posts"""
    
    class Meta:
        model = CommentP
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your comment...'}),
        }


class CommunitiesEventForm(forms.ModelForm):
    """Form for creating and editing community events"""
    
    class Meta:
        model = EventCalendar
        fields = ['name', 'start_date', 'end_date', 'location', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Name'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Location'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Event Description'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data

# ============================================
# MEMBERJOIN APP FORMS
# ============================================

class MembershipRegistrationForm(forms.ModelForm):
    """Form for membership registration"""
    
    class Meta:
        model = MembershipRegistration
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'country',
            'city', 'address', 'membership_type', 'organization_name', 'date_of_birth'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Phone Number'}),
            'country': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Country'}),
            'city': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'City'}),
            'address': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Address'}),
            'membership_type': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'organization_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Organization Name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'w-full border rounded-lg p-2', 'type': 'date'}),
        }


class ContactMessageForm(forms.ModelForm):
    """Form for contact messages"""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Your Email'}),
            'message': forms.Textarea(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Your Message', 'rows': 5}),
        }