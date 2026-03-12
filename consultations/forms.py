from django import forms
from .models import consultations


class ConsultationForm(forms.ModelForm):

    class Meta:
        model = consultations
        fields = [
            'full_name',
            'email',
            'phone',
            'country',
            'consultation_type',
            'description',
            'document'
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),

            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),

            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Country'
            }),

            'consultation_type': forms.Select(attrs={
                'class': 'form-control'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your legal issue'
            }),

            'document': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }