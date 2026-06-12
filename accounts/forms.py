from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import validate_email


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomerUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username or E-mail")
    remember_me = forms.BooleanField(required=False, label="Keep me signed in")


class UserForm(forms.ModelForm):
    password1 = forms.CharField(label="", widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label="", widget=forms.PasswordInput, required=True)

    class Meta:
        model = CustomerUser
        fields = [
            "category",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "country",
            "state",
            "city",
            "phone",
            "password1",
            "password2"
        ]
        labels = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone": "",
            "country": "",
            "state": "",
            "city": "",
            "password1": "",
            "password2": "",
        }

    # Check that password and password2 are the same.
    def clean_password2(self):
        """Ensure passwords match."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")

        # Validate email format
        if email:
            try:
                validate_email(email)
            except forms.ValidationError:
                self.add_error("email", "Invalid email address.")

        # Check for disallowed names
        disallowed_names = ["test", "testing"]
        for field in ["first_name", "last_name"]:
            value = cleaned_data.get(field, "").lower()
            if value in disallowed_names:
                self.add_error(field, f"This {field.replace('_', ' ')} is not allowed.")


    def save(self, commit=True):
        user = super().save(commit=False)

        # Automatically generate a username if it's not provided
        if not user.username:
            user.username = f"{user.first_name.lower()}{user.last_name.lower()}"

        # Make sure the username is unique
        user.username = self.generate_unique_username(user.username)
        
        # Hash password
        if self.cleaned_data.get("password2"):
            user.set_password(self.cleaned_data["password2"])

        if commit:
            user.save()
        return user
    

    def generate_unique_username(self, base_username):
        """
        This method will ensure that the username is unique.
        It will append a number if the username already exists.
        """
        username = base_username
        counter = 1
        while CustomerUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username


class OTPForm(forms.Form):
    # username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    # security_code = forms.CharField(
    #     widget=forms.OTPInput(attrs={"class": "form-control"})
    # )
    security_code = forms.CharField(label="OTP code")


class LoginForms(forms.Form):
    # username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class LoginForm(forms.Form):
    enter_your_username_or_email = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "username email"}
        )
    )
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
        username_or_email = cleaned_data.get("enter_your_username_or_email")
        password = cleaned_data.get("enter_your_password")
        # Add validation for required fields here
        # For example:
        if not username_or_email:
            self.add_error("enter_your_username_or_email", "This field is required.")
        if not password:
            self.add_error("password", "This field is required.")


# class MemberRegistrationForm(forms.ModelForm):
#     class Meta:
#         model = MemberRegistration
#         fields = ['email', 'first_name', 'last_name', 'gender', 'phone_number', 'country', 'city', 'agree']
#         widgets = {
#             'gender': forms.RadioSelect(choices=MemberRegistration.GENDER_CHOICES),
#             'agree': forms.CheckboxInput()
#         }
#         labels = {
#             'agree': 'I agree to the terms and conditions'
#         }


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name']


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['name', 'region']