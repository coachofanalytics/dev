from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.core.exceptions import ValidationError
import os
from .models import UserProfile, Category


def validate_file_extension(value, allowed_extensions):
    """Validate file extension against allowed list."""
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Unsupported file type. Allowed types: {", ".join(allowed_extensions)}'
        )


def validate_file_size(value, max_size_mb):
    """Validate file size doesn't exceed maximum."""
    max_size_bytes = max_size_mb * 1024 * 1024
    if value.size > max_size_bytes:
        raise ValidationError(f'File size cannot exceed {max_size_mb}MB.')


def validate_document(value):
    """Validate document uploads (PDF, DOC, DOCX)."""
    allowed_extensions = getattr(settings, 'ALLOWED_DOCUMENT_EXTENSIONS', ['.pdf', '.doc', '.docx'])
    max_size_mb = getattr(settings, 'MAX_DOCUMENT_SIZE_MB', 10)
    validate_file_extension(value, allowed_extensions)
    validate_file_size(value, max_size_mb)


def validate_image(value):
    """Validate image uploads."""
    allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
    max_size_mb = getattr(settings, 'MAX_IMAGE_SIZE_MB', 5)
    validate_file_extension(value, allowed_extensions)
    validate_file_size(value, max_size_mb)


class UserRegistrationForm(UserCreationForm):
    """
    Custom user registration form with additional fields including category, country, phone, and document upload.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),  # Lazy load - set in __init__ to avoid import-time DB queries
        required=True,
        empty_label='Select your category...',
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Select your registration category'
    )
    country = forms.ChoiceField(
        required=True,
        choices=[('', 'Select your country...')] + [
            ('Afghanistan', 'Afghanistan'),
            ('Albania', 'Albania'),
            ('Algeria', 'Algeria'),
            ('Andorra', 'Andorra'),
            ('Angola', 'Angola'),
            ('Antigua and Barbuda', 'Antigua and Barbuda'),
            ('Argentina', 'Argentina'),
            ('Armenia', 'Armenia'),
            ('Australia', 'Australia'),
            ('Austria', 'Austria'),
            ('Azerbaijan', 'Azerbaijan'),
            ('Bahamas', 'Bahamas'),
            ('Bahrain', 'Bahrain'),
            ('Bangladesh', 'Bangladesh'),
            ('Barbados', 'Barbados'),
            ('Belarus', 'Belarus'),
            ('Belgium', 'Belgium'),
            ('Belize', 'Belize'),
            ('Benin', 'Benin'),
            ('Bhutan', 'Bhutan'),
            ('Bolivia', 'Bolivia'),
            ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),
            ('Botswana', 'Botswana'),
            ('Brazil', 'Brazil'),
            ('Brunei', 'Brunei'),
            ('Bulgaria', 'Bulgaria'),
            ('Burkina Faso', 'Burkina Faso'),
            ('Burundi', 'Burundi'),
            ('Cabo Verde', 'Cabo Verde'),
            ('Cambodia', 'Cambodia'),
            ('Cameroon', 'Cameroon'),
            ('Canada', 'Canada'),
            ('Central African Republic', 'Central African Republic'),
            ('Chad', 'Chad'),
            ('Chile', 'Chile'),
            ('China', 'China'),
            ('Colombia', 'Colombia'),
            ('Comoros', 'Comoros'),
            ('Congo', 'Congo'),
            ('Costa Rica', 'Costa Rica'),
            ('Croatia', 'Croatia'),
            ('Cuba', 'Cuba'),
            ('Cyprus', 'Cyprus'),
            ('Czech Republic', 'Czech Republic'),
            ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'),
            ('Denmark', 'Denmark'),
            ('Djibouti', 'Djibouti'),
            ('Dominica', 'Dominica'),
            ('Dominican Republic', 'Dominican Republic'),
            ('East Timor', 'East Timor'),
            ('Ecuador', 'Ecuador'),
            ('Egypt', 'Egypt'),
            ('El Salvador', 'El Salvador'),
            ('Equatorial Guinea', 'Equatorial Guinea'),
            ('Eritrea', 'Eritrea'),
            ('Estonia', 'Estonia'),
            ('Eswatini', 'Eswatini'),
            ('Ethiopia', 'Ethiopia'),
            ('Fiji', 'Fiji'),
            ('Finland', 'Finland'),
            ('France', 'France'),
            ('Gabon', 'Gabon'),
            ('Gambia', 'Gambia'),
            ('Georgia', 'Georgia'),
            ('Germany', 'Germany'),
            ('Ghana', 'Ghana'),
            ('Greece', 'Greece'),
            ('Grenada', 'Grenada'),
            ('Guatemala', 'Guatemala'),
            ('Guinea', 'Guinea'),
            ('Guinea-Bissau', 'Guinea-Bissau'),
            ('Guyana', 'Guyana'),
            ('Haiti', 'Haiti'),
            ('Honduras', 'Honduras'),
            ('Hungary', 'Hungary'),
            ('Iceland', 'Iceland'),
            ('India', 'India'),
            ('Indonesia', 'Indonesia'),
            ('Iran', 'Iran'),
            ('Iraq', 'Iraq'),
            ('Ireland', 'Ireland'),
            ('Israel', 'Israel'),
            ('Italy', 'Italy'),
            ('Ivory Coast', 'Ivory Coast'),
            ('Jamaica', 'Jamaica'),
            ('Japan', 'Japan'),
            ('Jordan', 'Jordan'),
            ('Kazakhstan', 'Kazakhstan'),
            ('Kenya', 'Kenya'),
            ('Kiribati', 'Kiribati'),
            ('Kuwait', 'Kuwait'),
            ('Kyrgyzstan', 'Kyrgyzstan'),
            ('Laos', 'Laos'),
            ('Latvia', 'Latvia'),
            ('Lebanon', 'Lebanon'),
            ('Lesotho', 'Lesotho'),
            ('Liberia', 'Liberia'),
            ('Libya', 'Libya'),
            ('Liechtenstein', 'Liechtenstein'),
            ('Lithuania', 'Lithuania'),
            ('Luxembourg', 'Luxembourg'),
            ('Madagascar', 'Madagascar'),
            ('Malawi', 'Malawi'),
            ('Malaysia', 'Malaysia'),
            ('Maldives', 'Maldives'),
            ('Mali', 'Mali'),
            ('Malta', 'Malta'),
            ('Marshall Islands', 'Marshall Islands'),
            ('Mauritania', 'Mauritania'),
            ('Mauritius', 'Mauritius'),
            ('Mexico', 'Mexico'),
            ('Micronesia', 'Micronesia'),
            ('Moldova', 'Moldova'),
            ('Monaco', 'Monaco'),
            ('Mongolia', 'Mongolia'),
            ('Montenegro', 'Montenegro'),
            ('Morocco', 'Morocco'),
            ('Mozambique', 'Mozambique'),
            ('Myanmar', 'Myanmar'),
            ('Namibia', 'Namibia'),
            ('Nauru', 'Nauru'),
            ('Nepal', 'Nepal'),
            ('Netherlands', 'Netherlands'),
            ('New Zealand', 'New Zealand'),
            ('Nicaragua', 'Nicaragua'),
            ('Niger', 'Niger'),
            ('Nigeria', 'Nigeria'),
            ('North Korea', 'North Korea'),
            ('North Macedonia', 'North Macedonia'),
            ('Norway', 'Norway'),
            ('Oman', 'Oman'),
            ('Pakistan', 'Pakistan'),
            ('Palau', 'Palau'),
            ('Palestine', 'Palestine'),
            ('Panama', 'Panama'),
            ('Papua New Guinea', 'Papua New Guinea'),
            ('Paraguay', 'Paraguay'),
            ('Peru', 'Peru'),
            ('Philippines', 'Philippines'),
            ('Poland', 'Poland'),
            ('Portugal', 'Portugal'),
            ('Qatar', 'Qatar'),
            ('Romania', 'Romania'),
            ('Russia', 'Russia'),
            ('Rwanda', 'Rwanda'),
            ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),
            ('Saint Lucia', 'Saint Lucia'),
            ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),
            ('Samoa', 'Samoa'),
            ('San Marino', 'San Marino'),
            ('Sao Tome and Principe', 'Sao Tome and Principe'),
            ('Saudi Arabia', 'Saudi Arabia'),
            ('Senegal', 'Senegal'),
            ('Serbia', 'Serbia'),
            ('Seychelles', 'Seychelles'),
            ('Sierra Leone', 'Sierra Leone'),
            ('Singapore', 'Singapore'),
            ('Slovakia', 'Slovakia'),
            ('Slovenia', 'Slovenia'),
            ('Solomon Islands', 'Solomon Islands'),
            ('Somalia', 'Somalia'),
            ('South Africa', 'South Africa'),
            ('South Korea', 'South Korea'),
            ('South Sudan', 'South Sudan'),
            ('Spain', 'Spain'),
            ('Sri Lanka', 'Sri Lanka'),
            ('Sudan', 'Sudan'),
            ('Suriname', 'Suriname'),
            ('Sweden', 'Sweden'),
            ('Switzerland', 'Switzerland'),
            ('Syria', 'Syria'),
            ('Tajikistan', 'Tajikistan'),
            ('Tanzania', 'Tanzania'),
            ('Thailand', 'Thailand'),
            ('Togo', 'Togo'),
            ('Tonga', 'Tonga'),
            ('Trinidad and Tobago', 'Trinidad and Tobago'),
            ('Tunisia', 'Tunisia'),
            ('Turkey', 'Turkey'),
            ('Turkmenistan', 'Turkmenistan'),
            ('Tuvalu', 'Tuvalu'),
            ('Uganda', 'Uganda'),
            ('Ukraine', 'Ukraine'),
            ('United Arab Emirates', 'United Arab Emirates'),
            ('United Kingdom', 'United Kingdom'),
            ('United States', 'United States'),
            ('Uruguay', 'Uruguay'),
            ('Uzbekistan', 'Uzbekistan'),
            ('Vanuatu', 'Vanuatu'),
            ('Vatican City', 'Vatican City'),
            ('Venezuela', 'Venezuela'),
            ('Vietnam', 'Vietnam'),
            ('Yemen', 'Yemen'),
            ('Zambia', 'Zambia'),
            ('Zimbabwe', 'Zimbabwe'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_country'
        }),
        help_text='Select your country'
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
            'id': 'id_phone'
        }),
        help_text='Enter your phone number (country code will be added automatically)'
    )
    document = forms.FileField(
        required=True,
        validators=[validate_document],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx'
        }),
        help_text='Upload your resume/business profile (Required - PDF, DOC, DOCX, max 10MB)'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'category', 'document', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        # Set category queryset at runtime to avoid import-time DB queries (Heroku deployment fix)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Re-enter your password'
        })

    def clean_username(self):
        """
        Validate that the username is unique (case-insensitive) and normalize to lowercase.
        """
        username = self.cleaned_data.get('username')
        if username:
            # Normalize to lowercase
            username = username.lower()
            # Check if username exists (case-insensitive)
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        """
        Validate that the email is unique (case-insensitive) and normalize to lowercase.
        """
        email = self.cleaned_data.get('email')
        if email:
            # Normalize to lowercase
            email = email.lower()
            # Check if email exists (case-insensitive)
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('This email address is already registered.')
        return email

    def save(self, commit=True):
        """
        Save the user with the email field and profile information.
        """
        user = super(UserRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Update the user's profile with category, country, phone, and document
            profile = user.profile
            profile.category = self.cleaned_data['category']
            profile.country = self.cleaned_data['country']
            profile.phone = self.cleaned_data['phone']
            if self.cleaned_data.get('document'):
                profile.document = self.cleaned_data['document']
            profile.save()

        return user


class ProfileEditForm(forms.ModelForm):
    """
    Form for users to edit their profile information.
    """
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )

    class Meta:
        model = UserProfile
        fields = [
            'profile_image', 'bio', 'company_name', 'job_title',
            'phone', 'alternate_email', 'location', 'address',
            'website', 'linkedin_url', 'twitter_handle', 'facebook_url',
            'years_of_experience', 'industry', 'skills', 'document'
        ]
        widgets = {
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif,.webp'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself or your business'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company or Organization name'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CEO, Manager, Developer'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'alternate_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'alternative.email@example.com'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Full address (optional)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.example.com'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.linkedin.com/in/yourprofile'
            }),
            'twitter_handle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'yourusername (without @)'
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.facebook.com/yourprofile'
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5',
                'min': '0'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Technology, Finance, Healthcare'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g., Python, Django, Project Management, Marketing'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean_profile_image(self):
        """Validate profile image upload."""
        image = self.cleaned_data.get('profile_image')
        if image and hasattr(image, 'name'):
            validate_image(image)
        return image

    def clean_document(self):
        """Validate document upload."""
        document = self.cleaned_data.get('document')
        if document and hasattr(document, 'name'):
            validate_document(document)
        return document

    def save(self, commit=True):
        profile = super(ProfileEditForm, self).save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', self.user.email)
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
