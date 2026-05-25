from django import forms
from django.utils import timezone
from .models import Feedback, GetHelp, Governance, AppointmentRequest, Scholarship, TrainingCourse

class ContactForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            "user",
            # "category",
            # "sub_category",
            "topic",
            "description",
        ]
        labels = {
            "user": "Staff/Employee",
            # "category": "Pick your Category</h2>",
            # "subcategory": "Are You a Client/Staff?(Select Other if None of the above)",
            "topic": "Type your topic",
            "description": "Describe your issue or question in detail",
        }

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['user'].required=False
        self.fields['topic'].required=False
        # self.fields['category'].required=False
        # self.fields['sub_category'].required=False



class GetHelpForm(forms.ModelForm):
    class Meta:
        model = GetHelp
        fields = ['title', 'content','link']



class GovernanceForm(forms.ModelForm):
    class Meta:
        model = Governance
        fields = ['governance_category', 'title', 'description','members', 'region', 'chapter']


class SearchForm(forms.Form):
    specialty = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Specialty (e.g., Cardiologist, Dentist)',
        'class': 'search-input',
        'id': 'specialty-input',
    }))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Location (City or Country)',
        'class': 'search-input',
        'id': 'location-input',
    }))


class AppointmentRequestForm(forms.ModelForm):
    class Meta:
        model = AppointmentRequest
        fields = ['full_name', 'email', 'preferred_date', 'preferred_time', 'reason', 'honeypot']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com',
                'required': True,
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'preferred_time': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Briefly describe your reason for the appointment...',
                'required': True,
            }),
            'honeypot': forms.HiddenInput(),
        }


# ===== Education & Training Forms =====

class ScholarshipSearchForm(forms.Form):
    search_keyword = forms.CharField(required=False,
    widget=forms.TextInput(attrs={
        'class': 'w-full px-4 py-2 border border-gray-300 '
        'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
        'placeholder': 'Search By title, provider...'
    })
    )

    filter_level = forms.ChoiceField(required=False,
                   choices=[('', 'All Levels')] + Scholarship.Level.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )

    filter_field = forms.ChoiceField(required=False,
                   choices=[('', 'All Fields')] + Scholarship.Field.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    filter_location = forms.ChoiceField(required=False,
                   choices=[('', 'All Locations')] + Scholarship.Location.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    filter_currency = forms.ChoiceField(required=False,
                   choices=[('', 'All Currencies')] + Scholarship.Currency.choices,
                   widget=forms.Select(attrs={
                       'class': 'w-full px-4 py-2 border border-gray-300 '
                       'rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent',
                   })
                   )
    filter_status = forms.BooleanField(required=False,
                   label="Show only Closing Soon",
                   widget=forms.CheckboxInput(attrs={
                       'class': 'h-4 w-4 text-brand-blue focus:ring-brand-blue border-gray-300 rounded'
                   })
                   )


class ScholarshipForm(forms.ModelForm):
    class Meta:
        model = Scholarship
        fields = [
            'title',
            'provider',
            'level',
            'field',
            'location',
            'amount_value',
            'amount_description',
            'amount_currency',
            'deadline',
            'status'
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'provider': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'level': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'field': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'location': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'amount_value': forms.NumberInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'amount_description': forms.TextInput(attrs={'class': 'w-full border rounded-lg p-2'}),
            'amount_currency': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded-lg p-2'}),
            'status': forms.Select(attrs={'class': 'w-full border rounded-lg p-2'}),
        }


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = [
            "title",
            "course_code",
            "category",
            "description",
            "duration",
            "format",
            "enrollment",
            "max_students",
            "start_date",
            "end_date",
            "instructor",
            "price",
            "certificate_offered",
            "syllabus",
            "prerequisites",
            "image",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "syllabus": forms.Textarea(attrs={"rows": 3}),
            "prerequisites": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            })

    def clean_honeypot(self):
        value = self.cleaned_data.get('honeypot', '')
        if value:
            raise forms.ValidationError('Spam detected.')
        return value

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError('Please select a future date.')
        return date
