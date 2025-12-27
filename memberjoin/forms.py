
from django import forms
from .models import MembershipRegistration, ContactMessage

class MembershipRegistrationForm(forms.ModelForm):
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
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Your Email'}),
            'message': forms.Textarea(attrs={'class': 'w-full border rounded-lg p-2', 'placeholder': 'Your Message', 'rows': 5}),
        }