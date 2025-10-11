# Cursor AI Quick Context - CODA Platform

## 🎯 **FOR CURSOR AI: Quick Reference**

**Project**: CODA - Django 4.x multi-app platform with unified department dashboard system
**Key Pattern**: Single template serving multiple departments dynamically via `department_name` parameter

---

## 🏗️ **Core Architecture**

### **Organized App Structure (MANDATORY)**
```
app_name/
├── models/
│   ├── __init__.py
│   ├── core.py              # Core models
│   ├── domain1.py           # Domain-specific models
│   └── domain2.py           # Domain-specific models
├── views/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base.py          # Base view classes
│   │   └── dashboard.py     # Main dashboard views
│   ├── domain1/
│   │   ├── __init__.py
│   │   ├── dashboard.py     # Domain dashboard
│   │   ├── editing.py       # Domain editing
│   │   └── detail.py        # Domain detail views
│   └── api/
│       ├── __init__.py
│       └── domain1.py       # Domain APIs
├── services/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── base.py          # Base service classes
│   └── domain1/
│       ├── __init__.py
│       └── processing.py    # Domain services
├── forms/
│   ├── __init__.py
│   └── domain1.py           # Domain forms
└── utils/
    ├── __init__.py
    └── helpers.py           # Helper functions
```

### **Standard Django Structure**
```python
# Models (organized by domain)
class CoreModel(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

# Views (using base classes)
from .core.base import BaseView, login_required_domain

class DomainView(BaseView):
    def __init__(self):
        super().__init__()
    
    def get_context_data(self, request, **kwargs):
        # Business logic
        return {'title': 'Page Title', 'data': data}

@login_required_domain
def view_name(request, parameter=None):
    view = DomainView()
    try:
        context = view.get_context_data(request, parameter=parameter)
        return render(request, 'app/template.html', context)
    except Exception as e:
        view.handle_error(request, e, "Error message")
        return redirect('app:fallback-view')
```

---

## 🚨 **CRITICAL TEMPLATE REQUIREMENTS (MUST FOLLOW)**

### **Template Base Path (MANDATORY)**
```django
<!-- ALWAYS use this base template -->
{% extends "main/base_templates/new_base.html" %}

<!-- NEVER use -->
{% extends "base.html" %}  <!-- ❌ WRONG -->
```

### **Template Testing Requirements (MANDATORY)**
1. **ALWAYS test templates after creation** - Don't just create and deploy
2. **Test all buttons and links** - Click every button, test every URL
3. **Verify URL names exist** - Check that all `{% url %}` tags reference valid URL names
4. **Test with real data** - Use actual company slugs and IDs
5. **Check context variables** - Ensure all template variables are passed from views

### **Common Template Errors to Avoid**
```django
<!-- ❌ WRONG - Will cause NoReverseMatch -->
{% url 'non-existent-url-name' %}

<!-- ✅ CORRECT - Verify URL name exists in urls.py -->
{% url 'budget-category-detail' company.slug category.id %}

<!-- ❌ WRONG - Missing context variable -->
{{ data.category_id }}  <!-- If data.category_id doesn't exist -->

<!-- ✅ CORRECT - Check context structure -->
{{ category.id }}  <!-- If category is passed directly -->
```

### **Critical URL Names (VERIFY BEFORE USING)**
```python
# COMMON URL NAMES IN FINANCE APP:
'unified-budget-dashboard'    # NOT 'budget-dashboard'
'budget-category-detail'      # Budget drill-down
'budget-category-edit'        # Budget editing
'loan-eligibility-check'      # Loan eligibility
'loan-budget-dashboard'       # Loan dashboard
'smart-transaction-entry'     # Smart form
```

### **Template Testing Checklist**
- [ ] Template extends correct base: `main/base_templates/new_base.html`
- [ ] All `{% url %}` tags reference existing URL names (VERIFY IN urls.py)
- [ ] All template variables exist in context
- [ ] All buttons and links work when clicked
- [ ] Template renders without errors
- [ ] JavaScript functions work (if any)
- [ ] CSS classes are correct
- [ ] Forms submit correctly
- [ ] **CRITICAL**: Test locally before deploying

## 🎯 **ORGANIZED STRUCTURE BENEFITS**

### **Why This Structure?**
1. **Clear Separation of Concerns**: Each domain has its own models, views, services
2. **Scalable**: Easy to add new features without creating new files
3. **Maintainable**: Related code is grouped together
4. **Testable**: Each module can be tested independently
5. **Professional**: Follows Django best practices
6. **Reusable**: Base classes provide common functionality

### **Domain Organization Rules**
- **Core**: Fundamental models/views used across domains
- **Domain-specific**: Models/views specific to one business area
- **Services**: Business logic separated from views
- **Forms**: Domain-specific forms grouped together
- **APIs**: RESTful APIs organized by domain

### **File Naming Conventions**
- Models: `core.py`, `budget.py`, `loan.py`, `payment.py`
- Views: `dashboard.py`, `editing.py`, `detail.py`, `drilldown.py`
- Services: `estimation.py`, `consolidation.py`, `processing.py`
- Forms: `budget.py`, `loan.py`, `transaction.py`

### **Import Patterns**
```python
# Models
from .models.core import Budget, Transaction
from .models.budget import BudgetRequest, ApprovalPolicy

# Views
from .views.budget.dashboard import BudgetDashboardView
from .views.core.base import BaseView

# Services
from .services.budget.estimation import BudgetEstimationService
from .services.core.base import BaseService
```

## 🔐 **Security Requirements (ALWAYS INCLUDE)**

```python
# Authentication
from django.contrib.auth.decorators import login_required

# CSRF Protection
{% csrf_token %}  # In templates
headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value}  # AJAX

# Role-Based Access
def filter_links_by_role(links, user):
    filtered_links = []
    for link in links:
        has_access = True
        if 'admin/' in link.get('url', ''):
            has_access = user.is_staff or user.is_superuser
        if has_access:
            filtered_links.append(link)
    return filtered_links
```

---

## 🎨 **Frontend Standards**

### **Bootstrap 4.6.2 + Mobile-First**
```html
<div class="container-fluid">
    <div class="row">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header"><h5>Title</h5></div>
                <div class="card-body">Content</div>
            </div>
        </div>
    </div>
</div>

<!-- Template Inheritance -->
{% extends "main/base_templates/new_base.html" %}
{% load static %}

<!-- PWA Meta Tags -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#667eea">
```

**Key Libraries:**
- Bootstrap 4.6.2 (not Bootstrap 5)
- Font Awesome 4.7.0
- jQuery 3.6.4

### **JavaScript Patterns**
```javascript
$(document).ready(function() {
    // AJAX with CSRF
    $.ajax({
        url: '/api/endpoint/',
        method: 'POST',
        headers: {'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()},
        data: JSON.stringify(data),
        success: function(response) { /* handle */ },
        error: function(xhr, status, error) { /* handle */ }
    });
});
```

---

## 📊 **Database Patterns**

```python
# Optimization
queryset = Model.objects.select_related('foreign_key').prefetch_related('many_to_many')

# Filtering
queryset = Model.objects.filter(department__name='Finance', status='active')

# Always include indexes
class Meta:
    indexes = [models.Index(fields=['department', 'status'])]
```

---

## 🧪 **Testing Standards**

```python
from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
    
    def test_model_creation(self):
        # Test logic
        pass
```

---

## 🚀 **API Patterns**

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class ModelViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        try:
            instance = self.get_object()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

---

## 🎯 **Department Dashboard Requirements**

When working with department dashboards:

1. **Dynamic Content**: Use `department_name` parameter to customize content
2. **Role-Based Filtering**: Filter links and features by user permissions
3. **Real-Time Stats**: Display dynamic statistics from database
4. **Search Functionality**: Implement search across department links
5. **Mobile Responsive**: Ensure mobile-first design
6. **PWA Ready**: Include PWA meta tags

### **Department Configuration Pattern**
```python
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

---

## 🚀 **Mandatory Development Procedure**

**CRITICAL**: Follow this exact 7-step procedure for ALL development:

### **1. Codebase Review** 🔍
- Analyze existing models, views, templates, URLs
- Identify patterns and conventions
- Document current state

### **2. Requirements Analysis & Consolidation** 📋
- Compare requirements vs existing features
- Plan consolidation of models/views/templates
- Eliminate duplication and redundancy

### **3. Implementation Plan with Options** 🎯
- Create 2-3 implementation approaches
- Compare pros/cons, complexity, timeline
- Provide recommendation with justification

### **4. Phased Implementation with TTD** 🚀
- Break into logical, testable phases
- Write tests FIRST (TDD)
- **Realistic Test Data**: Create production-like test data:
  - Real department names (HR Department, Finance Department, IT Department)
  - Realistic amounts, dates, and business scenarios
  - Real user names and business context
  - Mimic real business use cases and requirements
- Comprehensive testing after each phase:
  - Unit, Integration, E2E, System, Performance, Security tests
- Do not proceed until phase passes all tests

### **5. Local Testing** 🧪
- Full application testing locally
- Cross-browser and device testing
- Performance and security testing

### **6. UAT Deployment** 🌐
- Deploy to Heroku UAT (`codamakutano`)
- Comprehensive UAT testing
- Stakeholder approval

### **7. Production Deployment** ⚠️
- **NEVER AUTO-DEPLOY** to production
- **Manual approval required**
- Update documentation

---

## 📚 **Documentation Structure**

**CRITICAL**: Organize docs as:
```
docs/app_name/Feature_Name/
├── README.md
├── REQUIREMENTS.md
├── IMPLEMENTATION.md
├── TESTING.md
└── DEPLOYMENT.md
```

**Examples:**
- `docs/finance/Budgeting/`
- `docs/accounts/User_Management/`
- `docs/ai_services/Analytics/`

---

## 🎯 **Realistic Test Data Requirements**

**CRITICAL**: Always create realistic, production-like test data to discover requirements and improve features.

### **Examples of Realistic vs Generic Data**

#### **Departments**
```python
# ❌ BAD: Generic
Department.objects.create(name="Test Department", slug="test")

# ✅ GOOD: Realistic
Department.objects.create(
    name="HR Department", 
    slug="hr",
    description="Human Resources and Employee Management"
)
```

#### **Budgets**
```python
# ❌ BAD: Generic
Budget.objects.create(amount=1000, category="test")

# ✅ GOOD: Realistic
Budget.objects.create(
    amount=150000.00,  # Realistic department budget
    category="HR Department",
    description="Annual HR Department Budget for 2024"
)
```

#### **Users**
```python
# ❌ BAD: Generic
User.objects.create(username="testuser", email="test@example.com")

# ✅ GOOD: Realistic
User.objects.create(
    username="john.smith",
    email="john.smith@company.com",
    first_name="John",
    last_name="Smith",
    category=1,  # HR category
    is_staff=True
)
```

### **Benefits**
- **Requirement Discovery**: Reveals missing requirements
- **Better Testing**: Tests real production scenarios
- **UX Improvement**: Identifies user experience issues
- **Business Logic**: Validates with real business rules

---

## 🚨 **CRITICAL REQUIREMENTS**

### **Always Include**
- ✅ `@login_required` for protected views
- ✅ CSRF tokens in forms and AJAX
- ✅ Try-catch blocks with logging
- ✅ Bootstrap 5 responsive design
- ✅ Role-based access control
- ✅ Optimized database queries
- ✅ Input validation

### **Never Do**
- ❌ Hardcode URLs (use `reverse()`)
- ❌ Skip input validation
- ❌ Ignore error handling
- ❌ Skip security measures
- ❌ Skip testing

---

## 📝 **Error Handling Pattern**

```python
import logging
logger = logging.getLogger(__name__)

try:
    # Main logic
    result = operation()
    return result
except ValidationError as e:
    logger.error(f"Validation error: {str(e)}")
    messages.error(request, 'Please check your input.')
except PermissionDenied:
    messages.error(request, 'Permission denied.')
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    messages.error(request, 'An error occurred.')
```

---

## 🎯 **Quick Development Checklist**

When generating code for CODA:

1. **Security**: Authentication + CSRF + role-based access
2. **Responsive**: Bootstrap 5 mobile-first design
3. **Performance**: Optimized queries with select_related/prefetch_related
4. **Error Handling**: Try-catch with proper logging
5. **Testing**: Include test cases
6. **Documentation**: Add docstrings
7. **Consistency**: Follow existing patterns
8. **Department Support**: Use unified dashboard patterns

**Remember**: CODA prioritizes security, performance, and user experience. All code should reflect these priorities.
