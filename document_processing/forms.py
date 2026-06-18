from django import forms
from.models import Document_Application
class Document_ApplicationForm(forms.ModelForm):
    class Meta:
        model=Document_Application
        field=['service','first_lenghth','last_name','id_number','district','sub_county','reason_form_request','fee',]