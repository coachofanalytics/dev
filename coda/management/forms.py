# from django.conf import settings
from django import forms
from django.forms import Textarea
from datetime import datetime
from professional_services.models import DSU,ClientAssessment,BackgroundCheck
from management.models import Assignment, Grievance, TaskLinks, Policy, Requirement, Task,TaskHistory,Meetings,TaskCategory
# from finance.models import Transaction, Inflow
from shared_core.users import Department
from accounts.models import UserProfile
from django import forms
# from captcha.fields import ReCaptchaV2CheckboxField  

class GrievanceForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = '__all__'
        
class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meetings
        fields = "__all__"
        widgets = {"meeting_description": Textarea(attrs={"cols": 40, "rows": 2})}

    def __init__(self, *args, **kwargs):
        super(MeetingForm, self).__init__(*args, **kwargs)
        # self.fields["name"].empty_label = "Select"

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "slug", "description", "is_active", "is_featured"]
        widgets = {"description": Textarea(attrs={"cols": 40, "rows": 2})}

    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        self.fields["name"].empty_label = "Select"

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = [
            "staff",
            # "first_name",
            # "last_name",
            "department",
            "day",
            "type",
            "description",
            "link",
            "policy_doc",
            "is_active",
            "is_featured",
            "is_internal",
        ]
        labels = {
            "staff": "User Name",
            "link": "Paste Link",
            "day": "Review Day",
            # "first_name": "First Name",
            # "last_name": "Last Name",
            "type": "Policy Type",
            "department": "Department",
            "description": "Description",
            "policy_doc": "Attach Policy",
        }
        widgets = {"description": Textarea(attrs={"cols": 75, "rows": 3})}



class ManagementForm(forms.ModelForm):
    class Meta:
        model = DSU
        # fields =['client','category','question_type','doc','link']
        fields = [
            "trained_by",
            "client_name",
            "type",
            "category",
            "task",
            "plan",
            "challenge",
            "uploaded",
        ]
        labels = {
            "type": "Client/Staff?",
            "client_name": "Manager",
            "trained_by": "Staff/Employee",
            "category": "Category",
            "task": "What Did You Work On?",
            "plan": "What is your next plan of action on areas that you have not touched on?",
            "challenge": "What specific questions/Challenges are you facing?",
            "uploaded": "Have you uploaded any DAF evidence/1-1 sessions?",
        }


class ClientAssessmentForm(forms.ModelForm):
    # captcha = ReCaptchaV2CheckboxField(
    # )
    class Meta:
        model = ClientAssessment
        fields = [
            # "clientname",
            "first_name",
            "last_name",
            "email",
            "education" ,
            # "rating_date",
            "skills",
            "experience",
            "non_it_exp",
            "it_exp",
            # "projectcharter",
            "projectmanagement",
            "requirementsAnalysis",
            "reporting",
            "etl",
            "database",
            "testing",
            "deployment",
            "frontend",
            "backend",
            # "totalpoints"
        ]
        labels = {
            "category": "Category",
            "type": "Client/Staff?",
            "first_name":"First Name",
            "last_name":"Last Name",
            "email":"Email",
            "education" : "Select your highest educational level?",
            "skills":"What other computer skills|Packages|certications do you have? ",
            "experience":"Describe any other experience you might have?",
            "non_it_exp":"How many years of Non IT Experience(Non IT Job)",
            "it_exp":"How many years of IT Experience(Work Experience)",
            "projectcharter":"Project Assessment",
            "requirementsAnalysis":"Business Analysis Role",
            "testing":"Testing",
            "etl":"(Alteryx,SSIS,Other)",
            "reporting":"Reprting(Powerbi,Tableau,Other)",
            "database":"Database(SQL,Oracle,Other)",
            "backend":"Backend(Python,Javascript,Other)",
            "frontend":"Front End(HTML,CSS,Editors)",
        }


class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = [
            # "created_by",
            "creator",
            "assigned_to",
            "requestor",
            "status",
            "company",
            "category",
            "app",
            "delivery_date",
            "duration",
            "what",
            "why",
            "how",
            "comments",
            "doc",
            "pptlink",
            "videolink",
            "is_active",
            "is_tested",
            "is_reviewed",
        ]

        labels = {
            "creator": "Creator",
            "assigned_to": "assigned_to",
            "requestor ": "Who needs it/beneficiary?",
            "app": "Specify app if Website",
            "company": "company",
            "category": "Select a category",
            "what": "Describe the Requirement",
            "why": "Why do they need it ?",
            "delivery_date": "When should this be delivered",
            "how": "Mode of delivery(website/Report/database?",
            "duration": "how long will it take to work on this requirement",
            "doc": "Upload Supporting Document",
            "pptlink": "Add link",
            "pptlink": "Add Video link",
            "is_tested": "Need Testing?",
        }
    # def __init__(self, **kwargs):
    #     super(RequirementForm, self).__init__(**kwargs)
    #     self.fields["created_by"].queryset = CustomerUser.objects.filter(
    #         is_staff=True
    #         # Q(is_staff=True)
    #     )

class EvidenceForm(forms.ModelForm):
    requirement = forms.ChoiceField(
        choices=[],  # Initialize with an empty list, will be populated dynamically
        required=False,
        label="Select Requirement"
    )
    
    class Meta:
        model = TaskLinks
        fields = [
            "task",
            "added_by",
            "link_name",
            "linkpassword",
            "description",
            "doc",
            "link",
            "is_active",
            "is_featured",
            "requirement",
        ]
        labels = {
            "task": "Task Name",
            "added_by": "Your Username",
            "link_name": "Enter Topic name",
            "linkpassword": "If Links Needs Password Enter Password here:",
            "description": "What is this link/Evidence about",
            "doc": "Upload file/document if possible",
            "link": "Upload link/paste your link below",
            "linkpassword": "Provide Password if necessary",
            "requirement": "Select Requirement",
        }
        widgets = {
            "description": Textarea(attrs={"cols": 60, "rows": 2}),
            "doc": forms.ClearableFileInput(attrs={'accept': 'image/*,application/pdf'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if request and request.user.is_authenticated:
            requirements = Requirement.objects.filter(assigned_to=request.user)
            requirement_choices = [(req.id, f"CODA000{req.id}") for req in requirements]
            requirement_choices.insert(0, ('', 'Select Requirement ID'))
            self.fields['requirement'].choices = requirement_choices

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
                   "group",
                    "category",
                    "employee",
                    "activity_name",
                    "description",
                    "point",
                    "mxpoint",
                    "mxearning",
        ]

        widgets = {"description": Textarea(attrs={"cols": 60, "rows": 2})}


class EmployeeContractForm(forms.ModelForm):
    national_id_no = forms.CharField(required=True)
    emergency_name = forms.CharField(required=True)
    emergency_address = forms.CharField(required=True)
    emergency_citizenship = forms.CharField(required=True)
    emergency_email = forms.CharField(required=True)
    emergency_phone = forms.CharField(required=True)
    emergency_national_id_no = forms.CharField(required=True)

    class Meta:
        model = UserProfile
        fields = ('national_id_no', 'id_file', 'emergency_name', 'emergency_address', 'emergency_citizenship', 'emergency_email', 'emergency_phone', 'emergency_national_id_no')

class BackgroundForm(forms.ModelForm):
    # national_id_no = forms.CharField(required=True)
    # emergency_name = forms.CharField(required=True)
    # emergency_address = forms.CharField(required=True)
    # emergency_citizenship = forms.CharField(required=True)
    # emergency_email = forms.CharField(required=True)
    # emergency_phone = forms.CharField(required=True)
    # emergency_national_id_no = forms.CharField(required=True)
    class Meta:
        model = BackgroundCheck
        fields="__all__"
        # fields=('candidate ','end_client','role','recruiting_agency','job_offer_letter','academic_documents','past_employers','reference_contacts','created_at ','status')

class TagFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=TaskCategory.objects.all(),
        label='Select a Category Tag'
    )

class MonthForm(forms.Form):
    MONTHS = (
        ('0', 'Month'),
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    )

    # Generate dynamic years (current year and last 4 years)
    current_year = datetime.now().year
    YEAR_CHOICES = [('0', 'Year')] + [
        (str(year), str(year)) for year in range(current_year, current_year - 4, -1)
    ]

    month = forms.ChoiceField(choices=MONTHS, required=True)
    year = forms.ChoiceField(choices=YEAR_CHOICES, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_date = datetime.now()
        self.fields['month'].initial = str(current_date.month)  # Default current month
        self.fields['year'].initial = str(current_date.year)  # Default current year


def dynamic_agenda_form(model_instance):
    class DynamicAgendaForm(forms.ModelForm):
        class Meta:
            model = model_instance.__class__
            fields = '__all__'
    return DynamicAgendaForm

class AssignmentUploadForm(forms.Form):
    files = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',  # Bootstrap styling for file input
        }),
        label='Select Files',
        required=True
    )


# ===== NEW OPTIMIZED MANAGEMENT FORMS =====

class OptimizedDepartmentForm(forms.Form):
    """Optimized form for department creation."""
    
    name = forms.CharField(
        label="Department Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department name'
        })
    )
    
    description = forms.CharField(
        label="Description",
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter department description'
        })
    )
    
    def clean_name(self):
        """Validate department name."""
        name = self.cleaned_data.get('name')
        if name and len(name) < 2:
            raise forms.ValidationError("Department name must be at least 2 characters long")
        return name


class OptimizedEmployeeForm(forms.Form):
    """Optimized form for employee creation."""
    
    first_name = forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    
    department_id = forms.IntegerField(
        label="Department",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    position = forms.CharField(
        label="Position",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter position title'
        })
    )
    
    salary = forms.DecimalField(
        label="Salary",
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter salary amount'
        })
    )
    
    def clean_email(self):
        """Validate email format."""
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise forms.ValidationError("Invalid email format")
        return email


class OptimizedMeetingForm(forms.Form):
    """Optimized form for meeting creation."""
    
    title = forms.CharField(
        label="Meeting Title",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter meeting title'
        })
    )
    
    description = forms.CharField(
        label="Description",
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter meeting description'
        })
    )
    
    meeting_date = forms.DateTimeField(
        label="Meeting Date & Time",
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    def clean_meeting_date(self):
        """Validate meeting date."""
        meeting_date = self.cleaned_data.get('meeting_date')
        if meeting_date and meeting_date < datetime.now():
            raise forms.ValidationError("Meeting date cannot be in the past")
        return meeting_date


class OptimizedPolicyForm(forms.Form):
    """Optimized form for policy creation."""
    
    CATEGORY_CHOICES = [
        ('hr', 'Human Resources'),
        ('safety', 'Safety'),
        ('it', 'Information Technology'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
        ('other', 'Other')
    ]
    
    title = forms.CharField(
        label="Policy Title",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter policy title'
        })
    )
    
    content = forms.CharField(
        label="Policy Content",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter policy content'
        })
    )
    
    category = forms.ChoiceField(
        label="Category",
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean_content(self):
        """Validate policy content."""
        content = self.cleaned_data.get('content')
        if content and len(content) < 50:
            raise forms.ValidationError("Policy content must be at least 50 characters long")
        return content


class OptimizedTaskForm(forms.Form):
    """Optimized form for task creation."""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    title = forms.CharField(
        label="Task Title",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter task title'
        })
    )
    
    description = forms.CharField(
        label="Description",
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter task description'
        })
    )
    
    assigned_to = forms.IntegerField(
        label="Assigned To",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        label="Priority",
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        label="Status",
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    due_date = forms.DateTimeField(
        label="Due Date",
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    def clean_title(self):
        """Validate task title."""
        title = self.cleaned_data.get('title')
        if title and len(title) < 3:
            raise forms.ValidationError("Task title must be at least 3 characters long")
        return title
    
    def clean_description(self):
        """Validate task description."""
        description = self.cleaned_data.get('description')
        if description and len(description) < 10:
            raise forms.ValidationError("Task description must be at least 10 characters long")
        return description