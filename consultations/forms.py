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

from django import forms
from .models import PreAssessment
class PreAssessmentForm(forms.ModelForm):
    class Meta:
        model = PreAssessment
        fields = '__all__'

from django import forms
from .models import PreAssessment


class PreAssessmentForm(forms.ModelForm):
    class Meta:
        model = PreAssessment
        fields = ['country', 'purpose', 'rejected_before', 'details']
        widgets = {
            'details': forms.Textarea(attrs={
                'class': 'form-control rounded-3 shadow-sm',  # adds shadow
                'style': 'background-color: #f9f9f9; box-shadow: 2px 2px 8px rgba(0,0,0,0.15);',
                'rows': 4,
                'placeholder': 'Enter additional details here...'
            }),
        }
        

from django import forms

class EligibilityForm(forms.Form):
    AGE_CHOICES = [
        ('under_18', 'Under 18'),
        ('18_35', '18-35'),
        ('36_60', '36-60'),
        ('60_plus', '60+'),
    ]

    age = forms.ChoiceField(choices=AGE_CHOICES)
    country = forms.CharField(max_length=100)
    years_of_residence = forms.IntegerField(min_value=0)
    
    married_to_citizen = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')]
    )

    has_ancestry = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')]
    )

    investment_budget = forms.IntegerField(
        required=False,
        help_text="Optional (USD)"
    )