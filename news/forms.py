from django import forms
from .models import NewsArticle

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