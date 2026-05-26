from django import forms
from django.utils import timezone
from .models import Feedback, GetHelp, Governance, AppointmentRequest

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


# ===== Healthcare Forms =====

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
