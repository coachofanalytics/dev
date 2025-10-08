from django import forms
from django.forms import Textarea
from django.core.validators import RegexValidator, validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import re

from .models import CustomerUser, Department, Credential, TaskGroup,CredentialCategory

# ------------------------------
# Helpers
# ------------------------------
phone_regex = r'^\d{10}$'

class AutocompleteEmailField(forms.EmailField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs['autocomplete'] = 'email'

# ------------------------------
# User Form
# ------------------------------
class UserForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repeat Password", widget=forms.PasswordInput)
    phone = forms.CharField(
        label="Phone",
        max_length=10,
        validators=[RegexValidator(regex=phone_regex, message="Phone number must be 10 digits (e.g., 5551234567).")],
    )
    email = AutocompleteEmailField()

    class Meta:
        model = CustomerUser
        fields = [
            "category", "sub_category", "first_name", "last_name", "username",
            "password1", "password2", "phone", "gender", "email", "address",
            "city", "state", "country", "zipcode", "resume_file", "is_staff", "is_applicant",
        ]
        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "username": "Username",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].initial = 1
        self.fields["sub_category"].initial = 1
        self.fields["gender"].required = True
        self.fields["country"].required = True

        if self.data.get("category") in ["3", "4", "5", "6"]:
            self.fields["username"].required = False
            self.fields["password1"].required = False
            self.fields["password2"].required = False
            self.fields["gender"].required = False
            self.fields["phone"].required = False

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("Invalid email address")
        return email    

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        username = cleaned_data.get("username")

        disallowed_usernames = ["test", "testing"]
        if first_name in disallowed_usernames:
            self.add_error("first_name", "This first name is not allowed.")
        if last_name in disallowed_usernames:
            self.add_error("last_name", "This last name is not allowed.")
        if username in disallowed_usernames:
            self.add_error("username", "This username is not allowed.")

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password2"):
            user.set_password(self.cleaned_data["password2"])
        if commit:
            user.save()
        return user

# ------------------------------
# Login Form
# ------------------------------
class LoginForm(forms.Form):
    enter_your_username_or_email = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username email"})
    )
    enter_your_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get("enter_your_username_or_email")
        password = cleaned_data.get("enter_your_password")

        if not username_or_email:
            self.add_error("enter_your_username_or_email", "This field is required.")
        if not password:
            self.add_error("enter_your_password", "This field is required.")

# ------------------------------
# Department Form
# ------------------------------
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["description", "slug", "is_featured", "is_active"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter department description"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "Slug (auto-generated if left blank)"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

# ------------------------------
# Credential Form
# ------------------------------
class CredentialForm(forms.ModelForm):
    class Meta:
        model = Credential
        fields = [
            "department",
            "added_by",
            "name",
            "slug",
            "description",
            "link_name",
            "link",
            "password",
            "entry_date",
            "is_active",
            "is_featured",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
            "entry_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }

# ------------------------------
# TaskGroup Form
# ------------------------------
class TaskGroupForm(forms.ModelForm):
    class Meta:
        model = TaskGroup
        fields = ["title", "description"]  # created_at auto-filled
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter task group title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter task group description"}),
        }

        from django import forms
from .models import TeamMember  # make sure your model is imported

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['category', 'title', 'description']

class credentialcategoryForm(forms.ModelForm):
    class Meta:
        model = CredentialCategory
        fields = ['description','verbose_name','entry_date','is_active','is_featured']