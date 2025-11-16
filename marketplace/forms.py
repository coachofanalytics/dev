from django import forms
from .models import BusinessProfile, InvestmentOpportunity, JobOpportunity
from django.utils import timezone
from datetime import timedelta


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = [
            "company_name", "industry", "company_size", "founded_date",
            "funding_stage", "investment_seeking", "equity_offered", "annual_revenue",
            "business_plan", "pitch_deck", "financial_statements"
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Company Name"}),
            "industry": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Technology, Healthcare"}),
            "company_size": forms.Select(attrs={"class": "form-select"}),
            "founded_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "funding_stage": forms.Select(attrs={"class": "form-select"}),
            "investment_seeking": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount in USD"}),
            "equity_offered": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Percentage (e.g., 15)"}),
            "annual_revenue": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Annual Revenue in USD"}),
            "business_plan": forms.FileInput(attrs={"class": "form-control"}),
            "pitch_deck": forms.FileInput(attrs={"class": "form-control"}),
            "financial_statements": forms.FileInput(attrs={"class": "form-control"}),
        }


class InvestmentOpportunityForm(forms.ModelForm):
    class Meta:
        model = InvestmentOpportunity
        fields = [
            "title", "description", "industry", "investment_type",
            "amount_seeking", "minimum_investment", "equity_percentage",
            "stage", "deadline"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Series A Funding for AI Platform"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the investment opportunity..."}),
            "industry": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Technology, Healthcare"}),
            "investment_type": forms.Select(attrs={"class": "form-select"}),
            "amount_seeking": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount in USD"}),
            "minimum_investment": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Minimum investment amount"}),
            "equity_percentage": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Equity percentage offered"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "deadline": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["deadline"].initial = timezone.now().date() + timedelta(days=90)


class JobOpportunityForm(forms.ModelForm):
    class Meta:
        model = JobOpportunity
        fields = [
            "title", "description", "requirements", "responsibilities",
            "job_type", "experience_level", "location", "remote_option",
            "salary_min", "salary_max", "salary_currency", "deadline"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Senior Software Engineer"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Job description..."}),
            "requirements": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Required skills and qualifications..."}),
            "responsibilities": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Key responsibilities..."}),
            "job_type": forms.Select(attrs={"class": "form-select"}),
            "experience_level": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Nairobi, Kenya"}),
            "remote_option": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "salary_min": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Minimum salary"}),
            "salary_max": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Maximum salary"}),
            "salary_currency": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., USD, KES"}),
            "deadline": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["deadline"].initial = timezone.now().date() + timedelta(days=60)
