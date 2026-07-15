#import Forms
from django import forms
from .models import Document_Application

class DocumentApplicationForm(forms.ModelForm):
    class Meta:
        model = Document_Application
        fields = ['user', 'service_type', 'reason', 'status', 'fee', 'first_name', 'last_name', 'id_number', 'district', 'sub_county', 'phone', 'email', 'notify_by_phone', 'notify_by_email', 'certified']
        