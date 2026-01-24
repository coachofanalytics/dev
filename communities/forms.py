from asyncio import Event
from django import forms
from django.utils import timezone
from .models import CommentP, CommunityMember, ContactMessage, Post, EventCalendar, DirectoryMember
from django import forms

class JoinForm(forms.ModelForm):
    class Meta:
        model = CommunityMember
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 rounded border', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-3 rounded border', 'placeholder': 'Your Email'}),
        }
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
class CommentForm(forms.ModelForm):
    class Meta:
        model = CommentP
        fields = ['content']
class EventForm(forms.ModelForm):
    class Meta:
        model = EventCalendar
        fields = ['name', 'start_date', 'end_date', 'location', 'description']

    # Optionally, you can add custom validations if needed
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        # If the field is empty, let the form's required validation handle it.
        if not start_date:
            return start_date

        if start_date <= timezone.now():
            raise forms.ValidationError("Start date must be in the future.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        # If either date is missing, skip this cross-field validation here.
        # The form-level validation or required field checks will handle missing values.
        if not end_date or not start_date:
            return end_date

        if end_date <= start_date:
            raise forms.ValidationError("End date must be after the start date.")
        return end_date
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']



# ============================================
# forms.py - Add these forms to your existing forms.py
# ============================================



class DirectoryMemberForm(forms.ModelForm):
    class Meta:
        model = DirectoryMember
        fields = ['full_name', 'profession', 'region', 'category', 
                  'membership_type', 'expertise', 'profile_photo']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Jane Doe'
            }),
            'profession': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Civil Engineer'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Seattle, WA'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'membership_type': forms.RadioSelect(attrs={
                'class': 'radio-input'
            }),
            'expertise': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Briefly describe your skills and what you offer to the community...',
                'rows': 4
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'file-input',
                'accept': 'image/*'
            })
        }


class EventUpdateForm(forms.ModelForm):
    class Meta:
        model = EventCalendar
        fields = ['name', 'start_date', 'end_date', 'location', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-brand-green',
                'placeholder': 'Event Name'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-brand-green',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-brand-green',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-brand-green',
                'placeholder': 'Location'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-brand-green',
                'placeholder': 'Description',
                'rows': 4
            })
        }