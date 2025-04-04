from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Textarea
from accounts.models import User,UserCategory
from .models import Feedback
from django.utils.translation import gettext_lazy as _

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


class FeedbackForm(forms.ModelForm):
    # category = forms.ModelChoiceField(queryset=UserCategory.objects.all())
    category = forms.ModelChoiceField(queryset=UserCategory.objects.all())
    sub_category = forms.ModelChoiceField(queryset=UserCategory.objects.all(), required=False)

    class Meta:
        model = Feedback
        fields = ['topic', 'description']

# class FeedbackForm(forms.ModelForm):
#     class Meta:
#         model = Feedback
#         fields = ("topic", "category", "sub_category", "description")
#     category = forms.ModelChoiceField(
#         queryset=UserCategory.objects.all(),
#         to_field_name='category',
#         label='Category',
#         widget=forms.Select(attrs={'class': 'form-control'}),
#     )
#     sub_category = forms.ModelChoiceField(
#         queryset=UserCategory.objects.all(),
#         to_field_name='sub_category',
#         label='Sub Category',
#         widget=forms.Select(attrs={'class': 'form-control'}),
#     )


from django import forms
from .models import GalleryImage  # Adjust the import according to your app structure

class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = '__all__'
