from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import validate_email
from .models import Membership

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomerUser
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username or E-mail")
    remember_me = forms.BooleanField(required=False, label="Keep me signed in")
class UserForm(forms.ModelForm):
    class Meta:
        model = CustomerUser
        fields = [
            "category",
           
            "first_name",
            "last_name",
            "email",
            "is_staff",
        ]
        labels = {
            
            "first_name": "",
            "last_name": "",
            "email": "",
        }
    
   
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
            user.username = f'{user.first_name.lower()}{user.last_name.lower()}'
        
        # Make sure the username is unique
        user.username = self.generate_unique_username(user.username)
        
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



class LoginForms(forms.Form):
    # username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
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
            self.add_error('password', "This field is required.") ,

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

class MembershipRegistrationForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="First Name", max_length=100, required=True)
    last_name = forms.CharField(label="Last Name", max_length=100, required=True)
    gender = forms.ChoiceField(label="Gender", choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], required=True)
    plan = forms.ChoiceField(label="Plan", choices=[
        ('1', 'Ordinary Member (Free)'),
        ('2', 'Active Members (1,000)'),
        ('3', 'Executive Members (10,000)'),
        ('4', 'Executive Members (10,000)'),
        ('5', 'ACTIVE ORGANIZATIONS (10,000)'),
        ('6', 'ROYAL ORGANIZATION (20,000)'),
    ], required=True)
    phone = forms.CharField(label="Phone Number", max_length=20, required=True)
    country = forms.CharField(label="Country", max_length=100, required=True)
    city = forms.CharField(label="City", max_length=100, required=True)
    accepted_terms = forms.BooleanField(label="I agree to the terms and conditions", required=True)