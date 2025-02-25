from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Textarea
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomerUser
from .models import Feedback, JobListing
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


from .models import membershirp_registration,MembershipPlan

 



class registrationform(forms.ModelForm):
    class Meta:
        model = membershirp_registration
        fields = '__all__'        





class MembershipPlanform(forms.ModelForm):
    class Meta:
        model = MembershipPlan
        fields = '__all__'        
        

class JoblistingForm(forms.ModelForm):
    class Meta:
        model = JobListing
        #fields = '__all__'
        fields = [
                'title',
                'description',
                'industry',
                'job_type',
                'location',
                'salary_range',
                'experience_level',
                'employer',
                'posted_at',
                'expires_at'
            ]



