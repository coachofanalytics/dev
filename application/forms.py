
from django import forms
from .models import JobApplication


class JobApplicationForm(forms.ModelForm):

    class Meta:
        model = JobApplication

        fields = [
            "full_name",
            "email",
            "phone",
            "cv",
            "cover_letter",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "cv": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": ".pdf,.doc,.docx"}
            ),
            "cover_letter": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
        }

    def clean_cv(self):
        cv = self.cleaned_data["cv"]
        allowed_extensions = (".pdf", ".doc", ".docx")

        if not cv.name.lower().endswith(allowed_extensions):
            raise forms.ValidationError(
                "Upload a PDF, DOC, or DOCX file."
            )

        if cv.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "The CV must not exceed 5 MB."
            )

        return cv
