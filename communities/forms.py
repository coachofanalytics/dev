
from django import forms
from django.utils import timezone
from .models import CommentP, CommunityMember, ContactMessage, Post, EventCalendar

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
        if start_date and start_date <= timezone.now():
            raise forms.ValidationError("Start date must be in the future.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        if end_date and end_date <= start_date:
            raise forms.ValidationError("End date must be after the start date.")
        return end_date
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']