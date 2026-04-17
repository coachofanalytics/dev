from django import forms
from .models import Taskmodel

class TaskForm(forms.ModelForm):
    class Meta:
        model = Taskmodel
        fields = ['title','description','is_completed']