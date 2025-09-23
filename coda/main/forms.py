from django import forms
from django.db.models import Q
from django.forms import ModelForm, Textarea
from accounts.models import CustomerUser
from .models import Testimonials
from django.utils.translation import gettext_lazy as _
# from .models import Expenses
from professional_services.models import DSU
from .models import *
# from django.db import transaction
# Optional import - removed during optimization to reduce slug size
try:
    from multiupload.fields import MultiFileField
    MULTIUPLOAD_AVAILABLE = True
except ImportError:
    MultiFileField = None
    MULTIUPLOAD_AVAILABLE = False

class ContactForm(forms.ModelForm):
    class Meta:
        model = DSU
        fields = [
            "trained_by",
            "client_name",
            "type",
            "category",
            "task",
            "plan",
            "challenge",
            "uploaded",
        ]
        labels = {
            "type": "Are You a Client/Staff?(Select Other if None of the above)",
            "client_name": "Manager",
            "trained_by": "Staff/Employee",
            "category": "Pick your Category</h2>",
            "task": "What Did You Work On?",
            "plan": "What is your next plan of action on areas that you have not touched on?",
            "challenge": "How Can We Help You?",
            "uploaded": "Have you uploaded any DAF evidence/1-1 sessions?",
        }

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['trained_by'].required=False
        self.fields['client_name'].required=False
        self.fields['type'].required=False
        self.fields['category'].required=False
        self.fields['task'].required=False
        self.fields['plan'].required=False
        self.fields['challenge'].required=False


class SearchForm(forms.ModelForm):
    # Define the choices for the category field
    category = forms.ChoiceField(choices=[("", "Select a category")] + Search.CAT_CHOICES)
    topic = forms.CharField(required=False,label='Pick a topic')
    class Meta:
        model = Search
        fields = [
            "searched_by",
            "category",
            "topic",
            "question",
            "uploaded",
        ]
        labels = {
            "searched_by": "Staff/Employee",
            "category": "Pick your Category",
            "topic": "Type a topic",
            "question": "Type a question related to the topic",
            "uploaded": "Have you uploaded any DAF evidence/1-1 sessions?",
        }
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['searched_by'].required=False
        self.fields['category'].required=True
        self.fields['topic'].required=False
        self.fields['question'].required=True

class PostForm(forms.ModelForm):
    class Meta:  
        model = Testimonials  
        # fields = ['writer', 'title', 'content']
        fields = ['title', 'content']
        widgets = {"content": Textarea(attrs={"cols": 40, "rows": 3})}

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        


# forms.py
class ClientAvailabilityForm(forms.ModelForm):
    class Meta:
        model = ClientAvailability
        fields = ['day', 'date', 'start_time', 'end_time', 'time_zone', 'category', 'subcategory', 'task', 'activity_links']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'category': forms.Select(attrs={'id': 'id_category', 'class': 'form-select'}),
            'subcategory': forms.Select(attrs={'id': 'id_subcategory', 'class': 'form-select'}),
            'task': forms.Select(attrs={'id': 'id_task', 'class': 'form-select'}),
            'activity_links': forms.Select(attrs={'id': 'id_activity_links', 'class': 'form-select'}),
        }
        
class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        # UPDATED: Use category-based filtering instead of deleted is_client field
        queryset=CustomerUser.objects.filter(
            Q(category__in=[1, 3, 4, 5, 6, 7]) | Q(is_staff=True)  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User + staff
        ),
        label='Select a client'
    )

class WCAG_Form(forms.Form):
    app_name= forms.ChoiceField(choices=[("", "Select a category")] + WCAGStandardWebsite.CAT_CHOICES)
    # app_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    company = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    page_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    website_url = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    # upload_file = forms.FileField()
    upload_multi_file = MultiFileField(max_file_size=1024*1024*5, min_num=1, max_num=3, required=True) if MULTIUPLOAD_AVAILABLE else forms.FileField()

    class Meta:
        model = WCAGStandardWebsite
        fields = ['company','app_name','upload_file', 'website_url', 'page_name']



class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name','sector', 'mission', 'website', 'location',  'description']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        location = cleaned_data.get('location')

        if Company.objects.filter(name=name, location=location).exists():
            raise forms.ValidationError('A company with this name and location already exists.')

        return cleaned_data
