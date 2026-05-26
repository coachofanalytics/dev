from django import forms
from .models import Feedback, GetHelp, Governance, NewsArticle

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



class GetHelpForm(forms.ModelForm):
    class Meta:
        model = GetHelp
        fields = ['title', 'content','link']



class GovernanceForm(forms.ModelForm):
    class Meta:
        model = Governance
        fields = ['governance_category', 'title', 'description','members', 'region', 'chapter']


class ArticleForm(forms.ModelForm):
    class Meta:
        model = NewsArticle
        fields = [
            'category', 'title', 'slug', 'author',
            'featured_image', 'content', 'ai_summary',
            'is_breaking', 'status', 'views'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'ai_summary': forms.Textarea(attrs={'rows': 3}),
        }
