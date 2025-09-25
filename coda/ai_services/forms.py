
from django import forms
from django.forms import Textarea
from ai_services.models import OpenaiPrompt, UpworkConnects,UseCase



class OpenaiForm(forms.ModelForm):
    class Meta:
        model = OpenaiPrompt
        fields = [
            "category",
            "subcategory",
            "topic",
            "expert_question" ,
            "role",
            "context_description",
            "clarification_description",
        ]
        # labels = {
        #     "category": "Category",
        #     "prompt": "Client/Staff?",
        #     "context":"First Name",
        #     "role":"Last Name",
        #     "clarifications":"Email",
        # }

class UpworkConnectsForm(forms.ModelForm):
    SKILL_CHOICES = [
        ('Python', 'Python'),
        ('SQL', 'SQL'),
        ('Web Scraping', 'Web Scraping'),
        ('React Native', 'React Native'),
        ('Django', 'Django'),
        ('Node.js', 'Node.js'),
        ('Database', 'Database'),
        ('MERN Stack', 'MERN Stack'),
        ('Web & Mobile Design Consultation', 'Web & Mobile Design Consultation'),
        ('Microsoft Power BI', 'Microsoft Power BI'),
        ('Tableau', 'Tableau'),
        ('React', 'React'),
        ('Automation', 'Automation')
    ]

    # Use a MultipleChoiceField for skills to allow multiple selections
    skills = forms.MultipleChoiceField(
        choices=SKILL_CHOICES, 
        widget=forms.CheckboxSelectMultiple(), 
        label="Required Skills"
    )

    class Meta:
        model = UpworkConnects
        fields = [
            'title', 
            'description', 
            'skills', 
            'payment_range', 
            'duration_range', 
            'project_type', 
            'project_category'
        ]
        widgets = {
            'payment_range': forms.Select(),
            'duration_range': forms.Select(),
            'project_type': forms.Select(),
            'project_category': forms.Select(),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'title': 'Job Title',
            'description': 'Job Description',
            'skills': 'Required Skills',
            'payment_range': 'Payment Range',
            'duration_range': 'Duration Range',
            'project_type': 'Project Type',
            'project_category': 'Project Category',
        }

    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        # Convert the list of skills to a comma-separated string
        return ",".join(skills)

class UseCaseForm(forms.ModelForm):
    class Meta:
        model = UseCase
        fields=['app','title', 'description', 'installation', 'usage_link', 'deployment', 'license', 'credits', 'contact', 'additional_sections', 'links']

 

class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()
  
#excel data fetching form    
class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField()
class MeetingForm(forms.Form):
    startDate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label="Start Date"
    )
    endDate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label="End Date"
    )     

# ==============================DIASPORA AI PLATFORM FORMS=============================

class RemittanceAnalysisForm(forms.Form):
    """Form for remittance analysis"""
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1500'})
    )
    frequency = forms.ChoiceField(
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destination = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kenya'})
    )
    purpose = forms.ChoiceField(
        choices=[
            ('family_support', 'Family Support'),
            ('investment', 'Investment'),
            ('education', 'Education'),
            ('business', 'Business'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    experience_years = forms.IntegerField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5'})
    )
    method = forms.ChoiceField(
        choices=[
            ('mobile_money', 'Mobile Money'),
            ('bank_transfer', 'Bank Transfer'),
            ('money_transfer', 'Money Transfer Service'),
            ('crypto', 'Cryptocurrency'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class TradeFacilitationForm(forms.Form):
    """Form for trade facilitation analysis"""
    business_type = forms.ChoiceField(
        choices=[
            ('import', 'Import'),
            ('export', 'Export'),
            ('both', 'Both Import & Export'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    product_categories = forms.MultipleChoiceField(
        choices=[
            ('agriculture', 'Agriculture'),
            ('textiles', 'Textiles'),
            ('manufacturing', 'Manufacturing'),
            ('services', 'Services'),
            ('technology', 'Technology'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    annual_volume = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000'})
    )
    target_markets = forms.MultipleChoiceField(
        choices=[
            ('USA', 'United States'),
            ('UK', 'United Kingdom'),
            ('Germany', 'Germany'),
            ('France', 'France'),
            ('Canada', 'Canada'),
            ('China', 'China'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    business_years = forms.IntegerField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '3'})
    )
    challenges = forms.MultipleChoiceField(
        choices=[
            ('logistics', 'Logistics'),
            ('regulations', 'Regulations'),
            ('financing', 'Financing'),
            ('market_access', 'Market Access'),
            ('competition', 'Competition'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

class InvestmentOpportunitiesForm(forms.Form):
    """Form for investment opportunities analysis"""
    investment_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=1000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '10000'})
    )
    risk_tolerance = forms.ChoiceField(
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    investment_horizon = forms.ChoiceField(
        choices=[
            ('1_year', '1 Year'),
            ('3_years', '3 Years'),
            ('5_years', '5 Years'),
            ('10_years', '10+ Years'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sector_interest = forms.MultipleChoiceField(
        choices=[
            ('real_estate', 'Real Estate'),
            ('agriculture', 'Agriculture'),
            ('technology', 'Technology'),
            ('manufacturing', 'Manufacturing'),
            ('services', 'Services'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    location_preference = forms.ChoiceField(
        choices=[
            ('Kenya', 'Kenya'),
            ('USA', 'United States'),
            ('UK', 'United Kingdom'),
            ('Canada', 'Canada'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class EducationPathwaysForm(forms.Form):
    """Form for education pathways analysis"""
    education_level = forms.ChoiceField(
        choices=[
            ('high_school', 'High School'),
            ('diploma', 'Diploma'),
            ('bachelor', 'Bachelor Degree'),
            ('master', 'Master Degree'),
            ('phd', 'PhD'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    field_interest = forms.ChoiceField(
        choices=[
            ('technology', 'Technology'),
            ('business', 'Business'),
            ('healthcare', 'Healthcare'),
            ('education', 'Education'),
            ('engineering', 'Engineering'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5000'})
    )
    location_preference = forms.ChoiceField(
        choices=[
            ('Kenya', 'Kenya'),
            ('USA', 'United States'),
            ('UK', 'United Kingdom'),
            ('Canada', 'Canada'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    time_commitment = forms.ChoiceField(
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('online', 'Online'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class HealthcareAccessForm(forms.Form):
    """Form for healthcare access analysis"""
    age_group = forms.ChoiceField(
        choices=[
            ('child', 'Child (0-17)'),
            ('adult', 'Adult (18-64)'),
            ('senior', 'Senior (65+)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    health_conditions = forms.MultipleChoiceField(
        choices=[
            ('diabetes', 'Diabetes'),
            ('hypertension', 'Hypertension'),
            ('heart_disease', 'Heart Disease'),
            ('cancer', 'Cancer'),
            ('mental_health', 'Mental Health'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    insurance_status = forms.ChoiceField(
        choices=[
            ('none', 'No Insurance'),
            ('private', 'Private Insurance'),
            ('public', 'Public Insurance'),
            ('employer', 'Employer Provided'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    location = forms.ChoiceField(
        choices=[
            ('Kenya', 'Kenya'),
            ('USA', 'United States'),
            ('UK', 'United Kingdom'),
            ('Canada', 'Canada'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2000'})
    )


# ===== NEW OPTIMIZED AI SERVICES FORMS =====

class OptimizedAnalysisForm(forms.Form):
    """Optimized form for data analysis requests."""
    
    DATA_TYPE_CHOICES = [
        ('csv', 'CSV Data'),
        ('json', 'JSON Data'),
        ('text', 'Text Data'),
        ('numerical', 'Numerical Data'),
        ('categorical', 'Categorical Data')
    ]
    
    data_type = forms.ChoiceField(
        label="Data Type",
        choices=DATA_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    confidence_threshold = forms.FloatField(
        label="Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        initial=0.8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.8'
        })
    )
    
    sample_size = forms.IntegerField(
        label="Sample Size",
        min_value=100,
        max_value=10000,
        initial=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1000'
        })
    )
    
    description = forms.CharField(
        label="Analysis Description",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe what you want to analyze'
        })
    )
    
    def clean_confidence_threshold(self):
        """Validate confidence threshold."""
        threshold = self.cleaned_data.get('confidence_threshold')
        if threshold and (threshold < 0.0 or threshold > 1.0):
            raise forms.ValidationError("Confidence threshold must be between 0.0 and 1.0")
        return threshold
    
    def clean_sample_size(self):
        """Validate sample size."""
        size = self.cleaned_data.get('sample_size')
        if size and size < 100:
            raise forms.ValidationError("Sample size must be at least 100")
        return size


class OptimizedDataUploadForm(forms.Form):
    """Optimized form for data file uploads."""
    
    FILE_TYPE_CHOICES = [
        ('csv', 'CSV File'),
        ('json', 'JSON File'),
        ('excel', 'Excel File'),
        ('txt', 'Text File')
    ]
    
    file = forms.FileField(
        label="Data File",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file',
            'accept': '.csv,.json,.xlsx,.xls,.txt'
        })
    )
    
    file_type = forms.ChoiceField(
        label="File Type",
        choices=FILE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        label="File Description",
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Describe the data in this file'
        })
    )
    
    is_public = forms.BooleanField(
        label="Make data public",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 10MB")
            
            # Check file extension
            allowed_extensions = ['.csv', '.json', '.xlsx', '.xls', '.txt']
            file_extension = '.' + file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"File type not supported. Allowed types: {', '.join(allowed_extensions)}")
        
        return file


class OptimizedModelConfigurationForm(forms.Form):
    """Optimized form for AI model configuration."""
    
    MODEL_CHOICES = [
        ('gpt-3.5', 'GPT-3.5'),
        ('gpt-4', 'GPT-4'),
        ('bert', 'BERT'),
        ('resnet', 'ResNet'),
        ('transformer', 'Transformer'),
        ('custom', 'Custom Model')
    ]
    
    model_name = forms.ChoiceField(
        label="Model Name",
        choices=MODEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    learning_rate = forms.FloatField(
        label="Learning Rate",
        min_value=0.0001,
        max_value=1.0,
        initial=0.001,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': '0.001'
        })
    )
    
    batch_size = forms.IntegerField(
        label="Batch Size",
        min_value=1,
        max_value=512,
        initial=32,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '32'
        })
    )
    
    epochs = forms.IntegerField(
        label="Epochs",
        min_value=1,
        max_value=1000,
        initial=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '100'
        })
    )
    
    dropout_rate = forms.FloatField(
        label="Dropout Rate",
        min_value=0.0,
        max_value=0.9,
        initial=0.2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.2'
        })
    )
    
    description = forms.CharField(
        label="Configuration Description",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe this model configuration'
        })
    )
    
    def clean_learning_rate(self):
        """Validate learning rate."""
        rate = self.cleaned_data.get('learning_rate')
        if rate and (rate < 0.0001 or rate > 1.0):
            raise forms.ValidationError("Learning rate must be between 0.0001 and 1.0")
        return rate
    
    def clean_batch_size(self):
        """Validate batch size."""
        size = self.cleaned_data.get('batch_size')
        if size and size < 1:
            raise forms.ValidationError("Batch size must be at least 1")
        return size
    
    def clean_epochs(self):
        """Validate epochs."""
        epochs = self.cleaned_data.get('epochs')
        if epochs and epochs < 1:
            raise forms.ValidationError("Epochs must be at least 1")
        return epochs