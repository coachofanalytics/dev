from django import forms
from .models import Testimonial, Feedback, Donation_organisation, Donation_organization, ContactMessage, Scholarship
from django.utils import timezone
from .models import AppointmentRequest
# Feedback / Contact Form

from .models import (
    ContactMessage, Scholarship, Governance, NewsArticle,TrainingCourse, GetHelp
)


class GetHelpForm(forms.ModelForm):
    class Meta:
        model = GetHelp
        fields = ['title', 'content','link']


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
    
    
    
class ScholarshipForm(forms.ModelForm):
    class Meta:
        model = Scholarship
        fields =  [
            'title',
            'provider',
            'level',
            'field',
            'location',
            'amount_value',
            'amount_description',
            'amount_currency',
            'deadline',
            'status'
        ]

        widgets = {
            'title':forms.TextInput(attrs={'class':'w-full border rounded-lg p-2'}),
            'provider':forms.TextInput(attrs={'class':'w-full border rounded-lg p-2'}),
            'level':forms.Select(attrs={'class':'w-full border rounded-lg p-2'}),
            'field':forms.Select(attrs={'class':'w-full border rounded-lg p-2'}),
            'location':forms.Select(attrs={'class':'w-full border rounded-lg p-2'}),
            'amount_value':forms.NumberInput(attrs={'class':'w-full border rounded-lg p-2'}),
            'amount_description':forms.TextInput(attrs={'class':'w-full border rounded-lg p-2'}),
            'amount_currency':forms.Select(attrs={'class':'w-full border rounded-lg p-2'}),
            'deadline':forms.DateInput(attrs={'type':'date'  ,'class':'w-full border rounded-lg p-2'}),
            'status':forms.Select(attrs={'class':'w-full border rounded-lg p-2'}),
        }



class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = [
            "title",
            "course_code",
            "category",
            "description",
            "duration",
            "format",
            "enrollment",
            "max_students",
            "start_date",
            "end_date",
            "instructor",
            "price",
            "certificate_offered",
            "syllabus",
            "prerequisites",
            "image",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "syllabus": forms.Textarea(attrs={"rows": 3}),
            "prerequisites": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            })


    
    


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
    




class ArticleForm(forms.ModelForm):
    class Meta:
        model = NewsArticle
        fields = [
            'category', 'title', 'author',
            'featured_image', 'content', 'ai_summary',
            'is_breaking', 'status',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'ai_summary': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category as NewsCategory
        self.fields['category'].queryset = NewsCategory.objects.all()
        self.fields['category'].empty_label = '-- Select a category --'


# ============================================
# COMMUNITIES APP FORMS (MERGED FROM communities app)
# ============================================
from .models import CommunityMember, DirectoryProfile, CommunityPost, CommentP, EventCalendar, CommunityMessage


class CommunityJoinForm(forms.ModelForm):
    agree_to_directory = forms.BooleanField(
        required=True,
        label="I agree to be listed in the public member directory"
    )

    email_updates = forms.BooleanField(
        required=False,
        initial=True,
        label="I want to receive community updates and opportunities via email"
    )

    agree_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy"
    )

    class Meta:
        model = CommunityMember
        fields = [
            'name', 'email', 'phone', 'profession', 'region',
            'specialization', 'bio', 'website'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': "Tell us about your professional background, expertise, and what you're looking for in the community..."
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+1 (555) 123-4567'
            }),
            'profession': forms.TextInput(attrs={
                'placeholder': 'e.g., Software Engineer, Lawyer, Doctor'
            }),
            'specialization': forms.TextInput(attrs={
                'placeholder': 'e.g., Web Development, Immigration Law, Finance'
            }),
            'website': forms.URLInput(attrs={
                'placeholder': 'https://linkedin.com/in/yourprofile or https://yourwebsite.com'
            }),
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'profession': 'Profession',
            'region': 'Region',
            'specialization': 'Specialization',
            'bio': 'Professional Bio',
            'website': 'Website or LinkedIn',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['profession'].required = True
        self.fields['region'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CommunityMember.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered in our community."
            )
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) < 10:
                raise forms.ValidationError(
                    "Please enter a valid phone number with area code."
                )
        return phone


class DirectoryProfileForm(forms.ModelForm):
    class Meta:
        model = DirectoryProfile
        fields = [
            'full_name', 'profession', 'region_city', 'category',
            'membership_type', 'expertise_summary', 'profile_photo'
        ]
        widgets = {
            'expertise_summary': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Briefly describe your skills and what you offer to the community...'
            }),
            'full_name': forms.TextInput(attrs={
                'placeholder': 'e.g., Jane Doe'
            }),
            'profession': forms.TextInput(attrs={
                'placeholder': 'e.g., Civil Engineer'
            }),
            'region_city': forms.TextInput(attrs={
                'placeholder': 'e.g., Seattle, WA'
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'region_city': 'Region / City',
            'expertise_summary': 'Expertise Summary',
            'profile_photo': 'Profile Photo',
        }


class CommunityPostForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ['title', 'content']


class CommunityCommentForm(forms.ModelForm):
    class Meta:
        model = CommentP
        fields = ['content']


class CommunityEventForm(forms.ModelForm):
    class Meta:
        model = EventCalendar
        fields = ['name', 'start_date', 'end_date', 'location', 'description']

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            return start_date
        if start_date <= timezone.now():
            raise forms.ValidationError("Start date must be in the future.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        if not end_date or not start_date:
            return end_date
        if end_date <= start_date:
            raise forms.ValidationError("End date must be after the start date.")
        return end_date


class CommunityContactForm(forms.ModelForm):
    """Contact form for community - uses existing ContactMessage model"""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']


class CommunityMessageForm(forms.ModelForm):
    """Form for sending messages between community directory members."""
    class Meta:
        model = CommunityMessage
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject (optional)',
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your message...',
            }),
        }
        labels = {
            'subject': 'Subject',
            'body': 'Message',
        }


class EmergencyHelpForm(forms.Form):
    """Form for submitting emergency help requests"""
    full_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address',
        })
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your phone number (optional)',
        })
    )
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Describe your emergency or help request...',
        })
    )
    urgency = forms.ChoiceField(
        choices=[('Emergency', 'Emergency'), ('Very Urgent', 'Very Urgent')],
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
