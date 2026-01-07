"""
Forms for social authentication onboarding.
"""
from django import forms
from accounts.models import Category


class SocialAuthCategoryForm(forms.Form):
    """
    Form for selecting category during social authentication.

    This form is shown to users who register via social auth (Google/Facebook)
    to allow them to select their user category.
    """
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=True,
        empty_label=None,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='I am joining as a:',
        help_text='Select the category that best describes you'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add descriptions for each category
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
