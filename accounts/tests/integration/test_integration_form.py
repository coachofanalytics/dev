from django import forms
from .models import Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["description", "slug", "is_featured", "is_active"]

        widgets = {
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter department description..."
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g finance, hr, operations"
            }),
            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug", "").strip().lower()

        if " " in slug:
            raise forms.ValidationError(
                "Slug should not contain spaces. Use hyphen or underscore."
            )

        return slug

