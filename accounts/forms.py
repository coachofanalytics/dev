from django import forms
from django.forms import Textarea
from accounts.choices import (
    UserCategory as CategoryChoices,
    ApplicantSubCategoryChoices,
    StudentSubCategoryChoices,
    ConsultantSubCategoryChoices,
    InvestorSubCategoryChoices,
    ExplorerSubCategoryChoices,
)
from .models import CustomerUser, CredentialCategory, Credential, LoginHistory
from django.core.validators import RegexValidator


class UserForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, required=True
    )
    password2 = forms.CharField(
        label="Repeat Password", widget=forms.PasswordInput, required=True
    )

    # Phone number validation
    # phone_regex = r'^\d{10}$'
    phone_regex = r"^(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$"
    # phone = forms.CharField(
    #     label="Phone",
    #     max_length=10,
    #     validators=[
    #         RegexValidator(
    #             regex=phone_regex,
    #             message="Phone number must be 10 digits (e.g., 5551234567).",
    #         )
    #     ],
    #     required=True
    # )
    # Robust phone number validation - accepts local and international formats
    phone = forms.CharField(
        label="Phone",
        max_length=20,  # Increased for international numbers
        validators=[
            RegexValidator(
                regex=phone_regex,
                message="Please enter a valid phone number (e.g., 1234567890, +1-234-567-8900, (234) 567-8900)",
            )
        ],
        required=True,
        help_text="Enter phone number with or without country code",
    )
    email = forms.EmailField(required=True)

    category = forms.ChoiceField(
        choices=[("", "Select Category")] + list(CategoryChoices.choices),
        widget=forms.Select(
            attrs={
                "class": "form-control"
                # Removed onchange - handled by external JS
            }
        ),
        required=True,
    )
    sub_category = forms.ChoiceField(
        choices=[("", "Select Sub Category")]
        + list(ApplicantSubCategoryChoices.choices),  # Start with Applicant choices
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
        initial="",
    )
    # sub_category = forms.ChoiceField(
    #     choices=[('', 'Select Sub Category')],
    #     widget=forms.Select(attrs={
    #         "class": "form-control"
    #         # Removed onchange - handled by external JS
    #     }),
    #     required=False,
    #     initial=''
    # )

    class Meta:
        model = CustomerUser
        fields = [
            "category",
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
        ]
        labels = {
            "sub_category": "",
            "first_name": "",
            "last_name": "",
            "username": "",
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

        # Set required fields dynamically
        for field in [
            "username",
            "password1",
            "password2",
            "phone",
            "gender",
            "country",
        ]:
            self.fields[field].required = True

    def get_choices_data(self):
        """Return choices data for JavaScript"""
        return {
            "categories": list(CategoryChoices.choices),
            "subcategories": {
                1: list(ApplicantSubCategoryChoices.choices),
                2: list(StudentSubCategoryChoices.choices),
                3: list(ConsultantSubCategoryChoices.choices),
                4: list(InvestorSubCategoryChoices.choices),
                5: list(ExplorerSubCategoryChoices.choices),
                6: list(InvestorSubCategoryChoices.choices),
                5: list(ExplorerSubCategoryChoices.choices),
            },
        }

    def update_subcategory_choices(self, category_id):
        """Update subcategory choices based on selected category"""
        if category_id and category_id.isdigit():
            cat_id = int(category_id)
            if cat_id == 1:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(ApplicantSubCategoryChoices.choices)
            elif cat_id == 2:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(StudentSubCategoryChoices.choices)
            elif cat_id == 3:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(ConsultantSubCategoryChoices.choices)
            elif cat_id == 4:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(InvestorSubCategoryChoices.choices)
            elif cat_id == 5:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(ExplorerSubCategoryChoices.choices)
            elif cat_id == 6:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(InvestorSubCategoryChoices.choices)
            elif cat_id == 7:
                self.fields["sub_category"].choices = [
                    ("", "Select Sub Category")
                ] + list(ExplorerSubCategoryChoices.choices)
            else:
                self.fields["sub_category"].choices = [("", "Select Sub Category")]
        else:
            self.fields["sub_category"].choices = [("", "Select Sub Category")]


class LoginHistoryForm(forms.ModelForm):
    login_time = forms.DateTimeField(input_formats=["%Y-%m-%d %I:%M %p"])
    logout_time = forms.DateTimeField(input_formats=["%Y-%m-%d %I:%M %p"])

    class Meta:
        model = LoginHistory
        fields = ["login_time", "logout_time"]


# ==========================CREDENTIAL FORM================================
class CredentialCategoryForm(forms.ModelForm):
    class Meta:
        model = CredentialCategory
        fields = [
            "department",
            "category",
            "slug",
            "description",
            "is_active",
            "is_featured",
        ]
        widgets = {
            # Use SelectMultiple below
            "category": forms.SelectMultiple(
                attrs={"class": "form-control", "category": "category"}
            ),
            "description": Textarea(attrs={"cols": 40, "rows": 2}),
        }


class CredentialForm(forms.ModelForm):
    class Meta:
        model = Credential
        fields = [
            "category",
            "name",
            "added_by",
            "slug",
            "user_types",
            "description",
            "password",
            "link_name",
            "link",
            "is_active",
            "is_featured",
        ]
        labels = {
            "link_name": "username/email",
            "link": "Link/url",
            "user_types": "Specify Who Can Access this Credential?",
        }
        widgets = {
            # Use SelectMultiple below
            "category": forms.SelectMultiple(
                attrs={"class": "form-control", "id": "category"}
            ),
            "description": Textarea(attrs={"cols": 40, "rows": 2}),
        }


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
            # self.add_error('password', "This field is required.")
            self.add_error("enter_your_password", "This field is required.")
