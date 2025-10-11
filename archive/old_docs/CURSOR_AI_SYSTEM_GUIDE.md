# Cursor AI System Guide for CODA Platform Development

## 🎯 **IMPORTANT: This is a guide FOR Cursor AI, not for developers**

**Purpose**: This document provides Cursor AI with comprehensive context about the CODA platform development patterns, conventions, and requirements. When starting any new chat or development task, Cursor AI should reference this guide to understand how development should be done on this project.

---

## 🏗️ **Project Overview**

### **Platform**: CODA - Comprehensive Organizational Data Analytics
**Technology Stack**: Django 4.x, PostgreSQL/SQLite, Bootstrap 5, jQuery, AI Services
**Architecture**: Multi-app Django project with unified dashboard system

### **Core Philosophy**
- **AI-First Development**: Leverage AI assistance for productivity while maintaining code quality
- **Unified Dashboard System**: Single template serving multiple departments dynamically
- **Role-Based Access Control**: Implement proper authentication and authorization
- **Mobile-First Design**: Responsive design with PWA capabilities
- **Security-First**: Always implement proper security measures

---

## 📁 **Project Structure**

```
coda/
├── accounts/          # User management and authentication
├── ai_services/       # AI-powered services and analytics
├── application/       # Application management
├── coda_project/      # Main Django project settings
├── core/             # Core utilities and middleware
├── finance/          # Financial management and budgeting
├── investing/        # Investment tracking and analysis
├── main/             # Main application views and utilities
├── management/       # Management and HR operations
├── marketing/        # Marketing and campaign management
├── professional_services/ # Training and professional services
├── unified_dashboard/ # Unified dashboard system
└── templates/        # Global templates
```

### **Key Template Locations**
```
templates/
├── main/
│   ├── base_templates/
│   │   └── new_base.html          # Main base template
│   ├── navbar_templates/
│   └── footer_templates/
├── finance/
│   ├── base_dashboard.html        # Finance dashboard base
│   ├── budgets/                   # Budget-related templates
│   └── reports/                   # Financial reports
├── emails/
│   └── base_email.html           # Email template base
└── components/
    └── form.html                 # Reusable form components
```

---

## 🔧 **Development Patterns & Conventions**

### **1. Django App Structure**
```python
# Standard app structure
app_name/
├── models.py          # Database models
├── views.py           # Main views
├── views_[feature].py # Feature-specific views
├── urls.py            # URL patterns
├── forms.py           # Django forms
├── admin.py           # Admin configuration
├── services/          # Business logic services
├── utilities/         # Utility functions
├── templates/         # HTML templates
└── management/commands/ # Custom management commands
```

### **2. Model Patterns**
```python
# Standard model structure
class ModelName(models.Model):
    # Fields with proper choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Model Name'
        verbose_name_plural = 'Model Names'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('app:model-detail', args=[self.pk])
```

### **3. View Patterns**
```python
# Standard view structure (from actual codebase)
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)

@login_required
def budget(request, company_slug="coda"):
    """Budget view with proper error handling and context preparation"""
    try:
        # Fetch the company object based on the slug
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return redirect("some_error_view")  # Redirect to an error page if company doesn't exist

    # Fetch budgets for the company
    company_budgets = Budget.objects.filter(company=company)
    site_budgets = Budget.objects.filter(company=company, category__name="Web")

    # Calculate total budgets
    total_budget = sum(site.amount for site in company_budgets)
    total_site_budget = sum(site.amount for site in site_budgets)
    total_operation = total_budget - total_site_budget

    # Construct link URL
    link_url = reverse(
        "finance:site_budget_with_subcategory",
        kwargs={"company_slug": company_slug, "category": "Web", "subcategory": "all"},
    )

    # Prepare summary data
    summary = [
        {"title": "Total Budget", "value": total_budget, "link": ""},
        {"title": "Operations", "value": total_operation, "link": ""},
        {"title": "Web Development", "value": total_site_budget, "link": link_url},
    ]

    context = {
        "company_name": company.name,
        "budget_obj": company_budgets,
        "data": summary,
    }
    return render(request, "finance/budgets/budget.html", context)
```

### **4. URL Patterns**
```python
# Standard URL structure
from django.urls import path
from . import views

app_name = 'app_name'
urlpatterns = [
    path('', views.home, name='home'),
    path('feature/', views.feature_view, name='feature'),
    path('feature/<int:pk>/', views.feature_detail, name='feature-detail'),
    path('api/feature/', views.feature_api, name='feature-api'),
]
```

### **5. Template Patterns**
```html
<!-- Standard template structure -->
{% extends "main/base_templates/new_base.html" %}
{% load static %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<!-- Main content -->
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <!-- Content here -->
        </div>
    </div>
</div>
{% endblock %}
```

**Key Template Inheritance:**
- **Main Base**: `{% extends "main/base_templates/new_base.html" %}`
- **Finance Dashboard**: `{% extends "finance/base_dashboard.html" %}`
- **Email Templates**: `{% extends "emails/base_email.html" %}`

**Bootstrap Version**: Bootstrap 4.6.2 (not Bootstrap 5)

---

## 🎯 **Department Dashboard System**

### **Unified Department Dashboard**
The CODA platform uses a unified department dashboard system that serves all departments from a single template:

```python
# Department routing pattern
path('department/<str:department_name>/', views.unified_department_dashboard, name='unified-department-dashboard')

# Department configuration structure
department_configs = {
    'finance': {
        'name': 'Finance',
        'icon': 'fas fa-chart-line',
        'color': '#667eea',
        'sections': [...],
        'enhanced_features': [...]
    }
}
```

### **Key Requirements for Department Features**
- **Dynamic Content**: Content must adapt based on department_name parameter
- **Role-Based Access**: Filter content based on user permissions
- **Real-Time Stats**: Display dynamic statistics from database
- **Search Functionality**: Implement search across department links
- **Mobile Responsive**: Ensure mobile-first design
- **PWA Ready**: Include PWA meta tags and manifest

---

## 🔐 **Security & Authentication**

### **Authentication Requirements**
```python
# Always use login_required for protected views
from django.contrib.auth.decorators import login_required

@login_required
def protected_view(request):
    # View logic here
    pass
```

### **Permission Patterns**
```python
# Role-based access control
def filter_links_by_role(links, user):
    """Filter links based on user permissions"""
    filtered_links = []
    
    for link in links:
        has_access = True
        
        # Admin-only links
        if 'admin/' in link.get('url', ''):
            has_access = user.is_staff or user.is_superuser
        
        # Staff-only links
        if 'reports/' in link.get('url', ''):
            has_access = user.is_staff
            
        if has_access:
            filtered_links.append(link)
    
    return filtered_links
```

### **CSRF Protection**
```python
# Always include CSRF token in forms
{% csrf_token %}

# For AJAX requests
headers: {
    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
    'Content-Type': 'application/json',
}
```

---

## 🎨 **Frontend Standards**

### **Bootstrap 4.6.2 Integration**
```html
<!-- Standard Bootstrap structure -->
<div class="container-fluid">
    <div class="row">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title">Title</h5>
                </div>
                <div class="card-body">
                    <!-- Content -->
                </div>
            </div>
        </div>
    </div>
</div>
```

**Bootstrap Version**: 4.6.2 (not Bootstrap 5)
**Font Awesome**: 4.7.0
**jQuery**: 3.6.4

### **JavaScript Patterns**
```javascript
// Standard jQuery structure
$(document).ready(function() {
    // Initialize functionality
    initializeComponents();
    
    // Event handlers
    $('#button').on('click', function() {
        // Handle click
    });
    
    // AJAX patterns
    $.ajax({
        url: '/api/endpoint/',
        method: 'POST',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
        },
        data: JSON.stringify(data),
        success: function(response) {
            // Handle success
        },
        error: function(xhr, status, error) {
            // Handle error
        }
    });
});
```

### **CSS Standards**
```css
/* Use CSS custom properties for consistency */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #28a745;
    --danger-color: #dc3545;
}

/* Mobile-first responsive design */
@media (max-width: 768px) {
    /* Mobile styles */
}
```

---

## 📊 **Database Patterns**

### **Model Relationships**
```python
# Standard foreign key patterns (from actual codebase)
class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_guarantor', 'Pending Guarantor Approval'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('repaid', 'Repaid'),
        ('cancelled', 'Cancelled'),
    ]
    
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE)
    borrower = models.ForeignKey("accounts.CustomerUser", on_delete=models.CASCADE, related_name='loan_applications')
    guarantor = models.ForeignKey('accounts.CustomerUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='guaranteed_loans')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'
    
    def __str__(self):
        return f"Loan Application #{self.application_number}"
```

### **Query Optimization**
```python
# Use select_related and prefetch_related
queryset = Model.objects.select_related('foreign_key').prefetch_related('many_to_many')

# Efficient filtering
queryset = Model.objects.filter(
    department__name='Finance',
    status='active'
).select_related('department')
```

### **Migration Patterns**
```python
# Always create migrations for model changes
python manage.py makemigrations
python manage.py migrate
```

---

## 🧪 **Testing Standards**

### **Test Structure**
```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class ModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def test_model_creation(self):
        # Test model creation
        pass
    
    def test_model_validation(self):
        # Test model validation
        pass
```

### **View Testing**
```python
class ViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_view_requires_login(self):
        response = self.client.get(reverse('app:protected-view'))
        self.assertEqual(response.status_code, 302)
    
    def test_view_with_authentication(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('app:protected-view'))
        self.assertEqual(response.status_code, 200)
```

---

## 🚀 **API Development**

### **Django REST Framework Patterns**
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class ModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer
    
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """Custom API action"""
        try:
            instance = self.get_object()
            # Custom logic here
            return Response({'success': True})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
```

### **API Response Patterns**
```python
# Standard API response format
{
    "success": True,
    "data": {...},
    "message": "Operation completed successfully"
}

# Error response format
{
    "success": False,
    "error": "Error message",
    "details": {...}
}
```

---

## 📱 **Mobile & PWA Requirements**

### **PWA Meta Tags**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#667eea">
<meta name="description" content="CODA Platform - Department Dashboard">
<link rel="manifest" href="{% url 'app:manifest' %}">
```

### **Responsive Design**
```css
/* Mobile-first approach */
.container {
    padding: 15px;
}

@media (min-width: 768px) {
    .container {
        padding: 30px;
    }
}

@media (min-width: 1200px) {
    .container {
        max-width: 1140px;
        margin: 0 auto;
    }
}
```

---

## 🔧 **Error Handling**

### **Exception Handling Patterns**
```python
import logging

logger = logging.getLogger(__name__)

def function_with_error_handling():
    try:
        # Main logic
        result = risky_operation()
        return result
    except SpecificException as e:
        logger.error(f"Specific error occurred: {str(e)}")
        # Handle specific error
        return fallback_value
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        # Handle unexpected error
        raise
```

### **User-Friendly Error Messages**
```python
from django.contrib import messages

try:
    # Operation
    pass
except ValidationError as e:
    messages.error(request, 'Please check your input and try again.')
except PermissionDenied:
    messages.error(request, 'You do not have permission to perform this action.')
except Exception as e:
    logger.error(f"Error: {str(e)}")
    messages.error(request, 'An unexpected error occurred. Please try again.')
```

---

## 📝 **Documentation Standards**

### **Code Documentation**
```python
def function_name(param1, param2=None):
    """
    Brief description of what the function does.
    
    Args:
        param1 (str): Description of param1
        param2 (int, optional): Description of param2. Defaults to None.
        
    Returns:
        dict: Description of return value
        
    Raises:
        ValidationError: When input validation fails
        PermissionDenied: When user lacks required permissions
        
    Example:
        >>> result = function_name('test', 123)
        >>> print(result)
        {'success': True}
    """
    pass
```

### **Template Documentation**
```html
<!--
Template: app/template_name.html
Purpose: Description of template purpose
Dependencies: List of required CSS/JS files
Context Variables: List of expected context variables
-->
```

---

## 🎯 **Development Workflow**

### **Mandatory Development Procedure**
**CRITICAL**: All development must follow this exact 7-step procedure:

#### **Step 1: Codebase Review** 🔍
- **Analyze Current Codebase**: Thoroughly examine existing models, views, templates, and URLs
- **Identify Patterns**: Understand existing conventions and architectural decisions
- **Document Current State**: Note all existing features, dependencies, and integrations
- **Review Documentation**: Study existing documentation and comments

#### **Step 2: Requirements Analysis & Consolidation** 📋
- **Analyze Requirements**: Compare new requirements against existing features
- **Identify Enhancements**: Determine what needs to be improved or extended
- **Plan Consolidation**: Identify models, views, templates that can be consolidated
- **Eliminate Duplication**: Remove redundant code and create reusable components
- **Create Consolidation Plan**: Document what will be merged, refactored, or removed

#### **Step 3: Implementation Plan with Options** 🎯
- **Create Multiple Options**: Present 2-3 different implementation approaches
- **Option Comparison**: Detail pros/cons, complexity, timeline for each option
- **Resource Requirements**: Estimate time, effort, and dependencies for each option
- **Risk Assessment**: Identify potential risks and mitigation strategies
- **Recommendation**: Provide clear recommendation with justification

#### **Step 4: Phased Implementation with TTD** 🚀
- **Phase Planning**: Break implementation into logical, testable phases
- **Test-Driven Development**: Write tests FIRST, then implement features
- **Realistic Test Data**: Create realistic, production-like test data:
  - ✅ **Real Names**: Use actual department names (HR Department, Finance Department, IT Department)
  - ✅ **Real Scenarios**: Mimic real business scenarios and use cases
  - ✅ **Realistic Values**: Use realistic amounts, dates, and data ranges
  - ✅ **Business Context**: Include realistic business context and relationships
  - ✅ **User Stories**: Base test data on actual user stories and requirements
- **Phase Implementation**: Implement one phase at a time
- **Comprehensive Testing**: After each phase:
  - ✅ **Unit Tests**: Test individual components
  - ✅ **Integration Tests**: Test component interactions
  - ✅ **End-to-End Tests**: Test complete user workflows
  - ✅ **System Tests**: Test system integration
  - ✅ **Performance Tests**: Test performance and scalability
  - ✅ **Security Tests**: Test security vulnerabilities
- **Phase Approval**: Do not proceed to next phase until current phase passes all tests

#### **Step 5: Local Testing** 🧪
- **Full Application Testing**: Test entire application locally
- **Cross-Browser Testing**: Test on multiple browsers and devices
- **Performance Testing**: Verify performance meets requirements
- **Security Testing**: Conduct security vulnerability assessment
- **User Acceptance Testing**: Test with actual user scenarios

#### **Step 6: UAT Deployment** 🌐
- **Deploy to Heroku UAT**: Deploy to `codamakutano` environment
- **UAT Testing**: Comprehensive testing in UAT environment
- **Stakeholder Review**: Get approval from stakeholders
- **Bug Fixes**: Address any issues found in UAT
- **Final Validation**: Ensure all requirements are met

#### **Step 7: Production Deployment** ⚠️
- **NEVER AUTO-DEPLOY**: Production deployment only when explicitly instructed
- **Manual Approval Required**: Must receive explicit approval for production
- **Documentation Update**: Update all relevant documentation
- **Monitoring Setup**: Ensure proper monitoring is in place

### **Documentation Structure Requirements** 📚
**CRITICAL**: All documentation must be organized in the following structure:

```
docs/
├── app_name/                    # e.g., finance/, management/, ai_services/
│   ├── Feature_Name/           # e.g., Budgeting/, User_Management/
│   │   ├── README.md          # Feature overview and quick start
│   │   ├── REQUIREMENTS.md    # Detailed requirements
│   │   ├── IMPLEMENTATION.md  # Implementation details
│   │   ├── TESTING.md         # Testing procedures and results
│   │   ├── DEPLOYMENT.md      # Deployment procedures
│   │   └── API_REFERENCE.md   # API documentation (if applicable)
│   └── Use_Case_Name/         # e.g., Loan_Processing/, Analytics/
│       ├── README.md
│       ├── REQUIREMENTS.md
│       ├── IMPLEMENTATION.md
│       ├── TESTING.md
│       └── DEPLOYMENT.md
```

**Examples:**
- **Budgeting Feature**: `docs/finance/Budgeting/`
- **User Management**: `docs/accounts/User_Management/`
- **AI Analytics**: `docs/ai_services/Analytics/`
- **Loan Processing**: `docs/finance/Loan_Processing/`

### **Deployment Environments** 🌐
**CRITICAL**: Understand the deployment environment structure:

#### **Development Environment**
- **Local Development**: Developer's local machine
- **Purpose**: Initial development and testing
- **Database**: SQLite or local PostgreSQL
- **Settings**: `local_settings.py`

#### **UAT Environment (codamakutano)**
- **Platform**: Heroku UAT environment
- **Purpose**: User Acceptance Testing
- **Database**: Heroku PostgreSQL
- **Settings**: `heroku_settings.py`
- **URL**: `codamakutano.herokuapp.com` (or similar)

#### **Production Environment**
- **Platform**: Heroku Production
- **Purpose**: Live production system
- **Database**: Heroku PostgreSQL Production
- **Settings**: `prod_settings.py`
- **URL**: Production domain
- **⚠️ CRITICAL**: Never deploy to production without explicit instruction

### **Realistic Test Data Requirements** 🎯
**CRITICAL**: All test data must be realistic and production-like to discover requirements and improve existing features.

#### **Department Data Examples**
```python
# ❌ BAD: Generic test data
Department.objects.create(name="Test Department", slug="test")

# ✅ GOOD: Realistic department data
Department.objects.create(
    name="HR Department", 
    slug="hr",
    description="Human Resources and Employee Management"
)
Department.objects.create(
    name="Finance Department", 
    slug="finance",
    description="Financial Management and Budgeting"
)
Department.objects.create(
    name="IT Department", 
    slug="it",
    description="Information Technology and Systems"
)
```

#### **Budget Data Examples**
```python
# ❌ BAD: Generic amounts
Budget.objects.create(amount=1000, category="test")

# ✅ GOOD: Realistic budget data
Budget.objects.create(
    amount=150000.00,  # Realistic department budget
    category="HR Department",
    description="Annual HR Department Budget for 2024",
    fiscal_year=2024
)
Budget.objects.create(
    amount=75000.00,   # Realistic project budget
    category="IT Infrastructure",
    description="Q1 IT Infrastructure Upgrade Budget"
)
```

#### **User Data Examples**
```python
# ❌ BAD: Generic user data
User.objects.create(username="testuser", email="test@example.com")

# ✅ GOOD: Realistic user data
User.objects.create(
    username="john.smith",
    email="john.smith@company.com",
    first_name="John",
    last_name="Smith",
    category=1,  # HR category
    is_staff=True
)
User.objects.create(
    username="sarah.johnson",
    email="sarah.johnson@company.com",
    first_name="Sarah",
    last_name="Johnson",
    category=2,  # Finance category
    is_staff=False
)
```

#### **Business Scenario Examples**
```python
# ❌ BAD: Generic scenarios
BudgetRequest.objects.create(amount=500, reason="test")

# ✅ GOOD: Realistic business scenarios
BudgetRequest.objects.create(
    amount=25000.00,
    reason="HR Department - Employee Training Program",
    description="Annual employee training and development program",
    department="HR Department",
    requested_by="john.smith",
    priority="high"
)
BudgetRequest.objects.create(
    amount=15000.00,
    reason="IT Department - Server Upgrade",
    description="Upgrade production servers for better performance",
    department="IT Department",
    requested_by="sarah.johnson",
    priority="medium"
)
```

#### **Benefits of Realistic Test Data**
1. **Requirement Discovery**: Realistic data reveals missing requirements
2. **Better Testing**: Tests scenarios that actually occur in production
3. **User Experience**: Helps identify UX issues early
4. **Business Logic**: Validates business rules with real scenarios
5. **Edge Cases**: Discovers edge cases and boundary conditions
6. **Performance**: Tests with realistic data volumes
7. **Integration**: Validates integrations with realistic data structures

#### **Test Data Categories**
- **Departments**: HR, Finance, IT, Marketing, Operations, Legal
- **Users**: Real names, realistic roles, proper categorization
- **Budgets**: Realistic amounts, proper categories, fiscal years
- **Requests**: Real business scenarios, proper priorities, realistic descriptions
- **Transactions**: Realistic amounts, proper categorization, business context
- **Tasks**: Realistic deadlines, proper assignments, business context
- **Meetings**: Realistic schedules, proper participants, business agenda

### **Code Generation Guidelines**
When generating code for CODA platform:

1. **Follow Existing Patterns**: Always match existing code structure and conventions
2. **Include Error Handling**: Implement proper exception handling and logging
3. **Add Security**: Include authentication, authorization, and CSRF protection
4. **Make Responsive**: Ensure mobile-first responsive design
5. **Optimize Performance**: Use efficient database queries and caching
6. **Write Tests**: Include comprehensive test coverage
7. **Document Code**: Add proper docstrings and comments

---

## 🚨 **Critical Requirements**

### **Always Include**
- ✅ **Authentication**: `@login_required` for protected views
- ✅ **CSRF Protection**: Include CSRF tokens in forms and AJAX
- ✅ **Error Handling**: Try-catch blocks with proper logging
- ✅ **Mobile Responsive**: Bootstrap 5 responsive design
- ✅ **Role-Based Access**: Filter content based on user permissions
- ✅ **Performance**: Optimized database queries
- ✅ **Security**: Input validation and sanitization

### **Never Do**
- ❌ **Hardcode URLs**: Use Django URL reversing
- ❌ **Skip Validation**: Always validate user input
- ❌ **Ignore Errors**: Handle all exceptions properly
- ❌ **Skip Testing**: Write tests for all functionality
- ❌ **Ignore Security**: Always implement proper security measures
- ❌ **Skip Documentation**: Document all code and APIs

---

## 📊 **Performance Standards**

### **Database Optimization**
```python
# Use select_related for foreign keys
queryset = Model.objects.select_related('foreign_key')

# Use prefetch_related for many-to-many
queryset = Model.objects.prefetch_related('many_to_many')

# Use only() to limit fields
queryset = Model.objects.only('id', 'title')

# Use defer() to exclude heavy fields
queryset = Model.objects.defer('large_text_field')
```

### **Template Optimization**
```html
<!-- Use {% load %} efficiently -->
{% load static %}
{% load custom_tags %}

<!-- Cache expensive operations -->
{% load cache %}
{% cache 500 sidebar %}
    <!-- Expensive sidebar content -->
{% endcache %}
```

---

## 🎉 **Summary**

When developing for the CODA platform, Cursor AI should:

1. **Follow Django Best Practices**: Use proper patterns and conventions
2. **Implement Security**: Always include authentication and CSRF protection
3. **Ensure Responsiveness**: Mobile-first design with Bootstrap 5
4. **Optimize Performance**: Efficient database queries and caching
5. **Handle Errors**: Proper exception handling and user feedback
6. **Write Tests**: Comprehensive test coverage
7. **Document Code**: Clear documentation and comments
8. **Use Unified Dashboard**: Follow department dashboard patterns
9. **Implement Role-Based Access**: Filter content by user permissions
10. **Maintain Consistency**: Follow existing code patterns and structure

**Remember**: The CODA platform prioritizes security, performance, and user experience. All code should reflect these priorities while maintaining consistency with existing patterns and conventions.
