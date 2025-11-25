from django import forms
from shared_core.users import UserCategory as CategoryChoices, CustomerUser
from marketing.models import Ads,Whatsapp_Groups
from django.utils.translation import gettext_lazy as _
from django_countries.widgets import CountrySelectWidget


class WhatsappForm(forms.ModelForm):
    class Meta:
        model = Whatsapp_Groups #Whatsapp
        fields = [
                    "category",
                    "type",
                    "group_name",
                    "group_id",
                    "country",
                    "participants",
                    "is_active",
                    "is_featured",
        ]
        labels = {
                    "group_name":"Enter Whatsapp Group",
                    "group_id ":"Enter Whatsapp Group id",
                    "type":"ad_type",
        }
        widgets = {
            'country': CountrySelectWidget(),  
        }


class AdsForm(forms.ModelForm):
    is_featured = forms.BooleanField(widget=forms.CheckboxInput(attrs={'disabled': 'disabled'}), required = False)
    is_active = forms.BooleanField(widget=forms.CheckboxInput(attrs={'disabled': 'disabled'}), required = False)

    class Meta:
        model = Ads #Whatsapp
        fields = [
            "ad_title",
            "bulletin",
            "company",
            "short_name",
            "description",
            "company_site",
            "message",
            "meeting_link",
            "video_link",
            "signature",
            "image_name",
            "link",
            "is_active",
            "is_featured",
        ]
        labels = {
                    "image_name":"Select image_name",
                    "description":"What does your company do?",
                    "message":"Describe the ad message to be posted",
        }   
        
    def __init__(self, *args, **kwargs):
        
        is_superuser = kwargs.pop('user', None)
        
        super(AdsForm, self).__init__(*args, **kwargs)
        if is_superuser:
            self.fields['is_featured'].widget.attrs['disabled'] = False
            self.fields['is_active'].widget.attrs['disabled'] = False

            
## Form for updating user's categories
class UpdateUserCategoryForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=CustomerUser.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2', 'data-placeholder': 'Search by username or email'})
    )
    category = forms.ChoiceField(
        choices=CategoryChoices.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )