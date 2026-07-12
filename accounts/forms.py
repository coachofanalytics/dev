from django import forms
from django.forms import  Textarea
from .models import CustomerUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import  RegexValidator,validate_email
from django.core.exceptions import ValidationError
import re
# from django.db import transaction

phone_regex = r'^\d{10}$'
class AutocompleteEmailField(forms.EmailField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.attrs['autocomplete'] = 'email'

class UserForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repeat Password", widget=forms.PasswordInput)
    phone = forms.CharField(label="Phone",max_length=10,validators=[RegexValidator(
                regex=phone_regex,
                message="Phone number must be 10 digits (e.g., 5551234567).",),],)
    email = AutocompleteEmailField()

    class Meta:
        model = CustomerUser
        fields = [
            "sub_category",
            "first_name",
            "last_name",
            "username",
            "password1",
            "password2",
            "phone",
            "gender",
            "email",
            "address",
            "city",
            "state",
            "country",
            "zipcode",
            "resume_file",
            "is_staff",
            "is_applicant",
        ]
        labels = {
            "sub_category": "",
            "first_name": "First Name",
            "last_name": "Last Name",
            "username": "Username",
            "email": "",
            "gender": "",
            "phone": "",
            "address": "",
            "city": "",
            "state": "",
            "country": "",
            "zipcode": "",
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # self.fields['category'].required= True
        # set category initial=1 and added category
        # self.fields["category"].initial = 1
        self.fields["sub_category"].initial = 1
        self.fields["gender"].required = True
        self.fields["country"].required = True
        if self.data.get('category') in ['3', '4', '5', '6']:

            self.fields['username'].required = False
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['gender'].required = False
            self.fields['phone'].required = False
        

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    def clean_email(self):
        email = self.cleaned_data.get('email')
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

        # List of disallowed usernames
        disallowed_usernames = ["test", "testing"]

        if first_name in disallowed_usernames:
            self.add_error("first_name", "This first name is not allowed.")
        if last_name in disallowed_usernames:
            self.add_error("last_name", "This last name is not allowed.")
        if username in disallowed_usernames:
            self.add_error("username", "This username is not allowed.")

    def save(self, commit=True):
        
        user = super(UserForm, self).save(commit=False)
        
        if self.cleaned_data.get('password2'):
            user.set_password(self.cleaned_data["password2"])
        else:
            user.set_password(user.password2)
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    enter_your_username_or_email = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control","autocomplete": "username email"}))
    enter_your_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    # def clean_enter_your_username_or_email(self):
    #     username_or_email = self.cleaned_data.get('enter_your_username_or_email')
    #     # Add your validation logic for email format here
    #     # For example:
    #     if '@' not in username_or_email:
    #         raise forms.ValidationError("Please enter a valid email address.")
    #     return username_or_email

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('enter_your_username_or_email')
        password = cleaned_data.get('enter_your_password')
        # Add validation for required fields here
        # For example:
        if not username_or_email:
            self.add_error('enter_your_username_or_email', "This field is required.")
        if not password:
            self.add_error('password', "This field is required.")    