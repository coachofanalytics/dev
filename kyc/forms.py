"""
KYC Forms
"""
from django import forms
from .models import KYCDocument


class KYCDocumentUploadForm(forms.ModelForm):
    """Form for uploading KYC documents."""

    class Meta:
        model = KYCDocument
        fields = [
            'document_type',
            'document_file',
            'document_number',
            'issue_date',
            'expiry_date',
            'issuing_authority',
        ]
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'document_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
                'required': True,
            }),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ID number, Passport number',
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'issuing_authority': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Government of Kenya',
            }),
        }
        help_texts = {
            'document_file': 'Accepted formats: PDF, JPG, PNG, DOC, DOCX. Max size: 10MB',
            'document_number': 'Enter the ID or reference number on your document (optional)',
            'issue_date': 'When was this document issued?',
            'expiry_date': 'When does this document expire? (if applicable)',
        }

    def clean_document_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('document_file')

        if file:
            # Check file size (10MB max)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    'File size must not exceed 10MB.'
                )

            # Check file extension
            ext = file.name.split('.')[-1].lower()
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']

            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'File type .{ext} is not allowed. '
                    f'Allowed types: {", ".join(allowed_extensions)}'
                )

        return file


class KYCDocumentVerificationForm(forms.ModelForm):
    """Form for staff to verify KYC documents."""

    VERIFICATION_ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('under_review', 'Mark Under Review'),
    ]

    action = forms.ChoiceField(
        choices=VERIFICATION_ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True,
        label='Verification Decision'
    )

    class Meta:
        model = KYCDocument
        fields = ['verification_notes']
        widgets = {
            'verification_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter notes about your decision...',
            }),
        }

    def clean(self):
        """Validate that notes are provided for rejection."""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        notes = cleaned_data.get('verification_notes')

        if action == 'reject' and not notes:
            raise forms.ValidationError(
                'Verification notes are required when rejecting a document.'
            )

        return cleaned_data
