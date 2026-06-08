from django import forms
from django.utils import timezone
from .models import Feedback, GetHelp, Governance, CommunityMember, DirectoryProfile, CommunityPost, CommentP, EventCalendar, ContactMessage, CommunityMessage

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
        # self.fields['category'].required=False
        # self.fields['sub_category'].required=False



class GetHelpForm(forms.ModelForm):
    class Meta:
        model = GetHelp
        fields = ['title', 'content','link']



class GovernanceForm(forms.ModelForm):
    class Meta:
        model = Governance
        fields = ['governance_category', 'title', 'description','members', 'region', 'chapter']


# ============================================
# COMMUNITIES APP FORMS
# ============================================

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
