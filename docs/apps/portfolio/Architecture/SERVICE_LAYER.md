# Portfolio Service Layer Architecture

**Purpose:** Unified service pattern for all presentation logic  
**Location:** `coda/portfolio/services/`

## Overview

The service layer provides a consistent interface for generating presentation context across all projects. It follows the **Template Method Pattern** with a base class defining the structure and subclasses implementing project-specific details.

## Core Components

### 1. BasePresentationService

**File:** `portfolio/services/base_presentation.py`

The abstract base class that all project presentations inherit from.

```python
class BasePresentationService:
    """
    Base service for all project presentations.
    
    Subclasses MUST override:
    - project_name: str
    - project_slug: str
    - get_technologies(): dict
    - get_key_metrics(): dict
    - get_investor_context(): dict
    - get_technical_context(): dict
    
    Subclasses MAY override:
    - get_recruiter_context(): dict
    - get_demo_context(): dict
    - get_created_date(): str
    """
    
    project_name = "Override in subclass"
    project_slug = "override-in-subclass"
    
    def get_context(self, audience_type, presentation_mode='branded'):
        """
        Main method to get complete context for a presentation.
        
        Args:
            audience_type: 'investor', 'technical', 'recruiter', 'demo'
            presentation_mode: 'branded' or 'interview'
            
        Returns:
            dict: Complete context for template rendering
        """
```

### 2. ProjectRegistry

**Purpose:** Central registry for all presentation services

```python
class ProjectRegistry:
    """
    Singleton registry for managing all presentation services.
    """
    _services = {}
    
    @classmethod
    def register(cls, slug, service_class):
        """Register a presentation service"""
        cls._services[slug] = service_class
        
    @classmethod
    def get_service(cls, slug):
        """Get service instance for a project"""
        service_class = cls._services.get(slug)
        if service_class:
            return service_class()
        return None
        
    @classmethod
    def get_all_projects(cls):
        """Get metadata for all registered projects"""
        projects = []
        for slug, service_class in cls._services.items():
            service = service_class()
            projects.append({
                'slug': slug,
                'name': service.project_name,
                'technologies': service.get_technologies(),
                'metrics': service.get_key_metrics(),
            })
        return projects
```

## Project Service Pattern

### Minimal Implementation

```python
from .base_presentation import BasePresentationService, ProjectRegistry

class NewProjectPresentationService(BasePresentationService):
    """Service for New Project presentations"""
    
    # Required attributes
    project_name = "New Project Name"
    project_slug = "new-project"
    
    # Required methods
    def get_technologies(self):
        return {
            'backend': ['Django', 'PostgreSQL'],
            'frontend': ['React', 'TypeScript'],
            'ai_ml': ['TensorFlow', 'Scikit-learn'],
        }
    
    def get_key_metrics(self):
        return {
            'roi': '$100K+ annual savings',
            'performance': '99.9% uptime',
            'scale': '10M+ requests/day',
        }
    
    def get_investor_context(self):
        return {
            'market_size': '$5B TAM',
            'competitive_advantage': 'Proprietary AI algorithm',
            'revenue_model': 'SaaS subscription',
            'roi_scenarios': [
                {'size': 'Small', 'roi': '200%'},
                {'size': 'Enterprise', 'roi': '500%'},
            ],
        }
    
    def get_technical_context(self):
        return {
            'architecture': 'Microservices with event-driven design',
            'code_samples': [
                {
                    'title': 'Core Algorithm',
                    'file': 'services/algorithm.py',
                    'lines': '45-120',
                    'highlights': ['ML model', 'Real-time processing'],
                },
            ],
            'tech_challenges': [
                {
                    'challenge': 'Scaling to 10M daily users',
                    'solution': 'Implemented Redis caching and read replicas',
                    'impact': '10x performance improvement',
                },
            ],
        }
    
    def get_recruiter_context(self):
        """Optional: Override for recruiter-specific content"""
        return {
            'achievements': [
                'Built system from scratch in 3 months',
                'Reduced costs by 60%',
                'Improved user satisfaction by 40%',
            ],
            'skills_demonstrated': [
                'Full-stack development',
                'AI/ML integration',
                'System architecture',
                'Team leadership',
            ],
        }

# Register the service
ProjectRegistry.register('new-project', NewProjectPresentationService)
```

## Context Structure

### Base Context (All Presentations)

```python
{
    'project_name': str,
    'project_slug': str,
    'audience_type': str,
    'presentation_mode': str,  # 'branded' or 'interview'
    'show_branding': bool,
    'branding': {
        'company_name': str,
        'logo_url': str,
        'tagline': str,
        'contact': dict,
    },
    'technologies': dict,
    'key_metrics': dict,
    'created_date': str,
}
```

### Investor Context

```python
{
    # ... base context ...
    'market_size': str,
    'competitive_advantage': str,
    'revenue_model': str,
    'roi_scenarios': [
        {
            'size': str,
            'investment': str,
            'roi': str,
            'payback_months': int,
        },
    ],
    'financial_projections': dict,
    'go_to_market': str,
}
```

### Technical Context

```python
{
    # ... base context ...
    'architecture': str,
    'tech_stack': {
        'backend': list,
        'frontend': list,
        'infrastructure': list,
        'ai_ml': list,
    },
    'code_samples': [
        {
            'title': str,
            'file': str,
            'lines': str,
            'code': str,  # Optional: actual code snippet
            'highlights': list,
        },
    ],
    'tech_challenges': [
        {
            'challenge': str,
            'solution': str,
            'impact': str,
        },
    ],
    'test_coverage': str,
    'deployment': str,
}
```

### Recruiter Context

```python
{
    # ... base context ...
    'achievements': list,  # Bullet points of impact
    'skills_demonstrated': list,  # Technical skills
    'leadership': list,  # Leadership examples
    'timeline': [
        {
            'phase': str,
            'duration': str,
            'deliverables': list,
        },
    ],
    'impact_metrics': dict,
}
```

## Branding Logic

### Automatic Mode Detection

```python
def _get_branding(self, mode):
    """
    Generate branding context based on presentation mode.
    
    Mode is automatically determined by URL:
    - /portfolio/ → 'branded' (CODA)
    - /interview/ → 'interview' (white-label)
    """
    if mode == 'branded':
        return {
            'company_name': 'CODA Analytics',
            'logo_url': '/static/images/coda-logo.png',
            'tagline': 'Data-Driven Solutions',
            'contact': {
                'email': 'info@coda.com',
                'phone': '+254 XXX XXX XXX',
                'website': 'https://coda.com',
            }
        }
    else:  # interview mode
        from django.conf import settings
        return {
            'developer_name': getattr(settings, 'DEVELOPER_NAME', 'Developer'),
            'logo_url': '/static/images/portfolio-logo.png',
            'tagline': getattr(settings, 'DEVELOPER_TITLE', 'Full-Stack Engineer'),
            'contact': {
                'email': getattr(settings, 'DEVELOPER_EMAIL', 'email@example.com'),
                'linkedin': getattr(settings, 'DEVELOPER_LINKEDIN', ''),
                'github': getattr(settings, 'DEVELOPER_GITHUB', ''),
            }
        }
```

## Real Example: Budget Tier Service

**File:** `portfolio/services/budget_tier_presentation.py`

```python
class BudgetTierPresentationService(BasePresentationService):
    """Service for Budget Tier System presentations"""
    
    project_name = "AI-Driven Budget Tier System"
    project_slug = "budget-tier"
    
    def get_technologies(self):
        return {
            'backend': ['Django 4.x', 'PostgreSQL', 'Python 3.9+'],
            'ai_ml': [
                'Statistical Analysis',
                'Time Series Classification',
                'Pattern Recognition',
                'Variance Detection',
            ],
            'frontend': ['jQuery', 'Bootstrap 5', 'AJAX'],
            'infrastructure': ['Heroku', 'PostgreSQL on AWS'],
        }
    
    def get_key_metrics(self):
        return {
            'savings': '$50K+ annually',
            'automation': '75% approval automation',
            'accuracy': '95%+ prediction accuracy',
            'data_processed': '$1.49M in transactions',
            'categories': '17 budget categories',
            'time_to_deploy': '2 weeks',
        }
    
    def get_investor_context(self):
        return {
            'problem': 'Manual budget approvals waste 10-15 hours/month per organization',
            'solution': 'AI-driven approval routing with 75% automation rate',
            'market_size': '$2.5B enterprise budget management market',
            'competitive_advantage': 'Data-driven tier system, not rule-based',
            'revenue_model': 'SaaS subscription ($99-$499/month based on org size)',
            'roi_scenarios': [
                {
                    'size': 'Small Org (50 employees)',
                    'investment': '$1,188/year',
                    'savings': '$3,800/year',
                    'roi': '320%',
                    'payback_months': 3,
                },
                {
                    'size': 'Medium Org (500 employees)',
                    'investment': '$3,588/year',
                    'savings': '$25,000/year',
                    'roi': '697%',
                    'payback_months': 1.5,
                },
            ],
            'go_to_market': 'Target mid-sized nonprofits and enterprises',
        }
    
    def get_technical_context(self):
        return {
            'architecture': 'Layered Django architecture with service-driven AI logic',
            'tech_challenges': [
                {
                    'challenge': 'Classify 17 categories with limited historical data',
                    'solution': 'Statistical analysis of $1.49M in transaction data',
                    'impact': '95%+ accuracy in tier assignment',
                },
                {
                    'challenge': 'Avoid hardcoded approval rules',
                    'solution': 'Data-driven tier system with configurable thresholds',
                    'impact': '75% automation rate, easily adjustable',
                },
            ],
            'code_samples': [
                {
                    'title': 'AI Tier Classification Algorithm',
                    'file': 'finance/management/commands/classify_budget_category_tiers.py',
                    'lines': '40-120',
                    'highlights': [
                        'Statistical quartile analysis',
                        'Recurring pattern detection',
                        'Variance threshold calculation',
                    ],
                },
                {
                    'title': 'Smart Approval Service',
                    'file': 'finance/services/smart_approval_service.py',
                    'lines': '25-85',
                    'highlights': [
                        'Auto-approval logic',
                        'Tier-based routing',
                        'Variance checking',
                    ],
                },
            ],
            'test_coverage': '40 comprehensive tests across models, services, views',
            'deployment': 'Heroku with PostgreSQL, CI/CD via Git',
        }
    
    def get_recruiter_context(self):
        return {
            'achievements': [
                'Built complete AI system in 2 weeks',
                'Analyzed $1.49M in real financial data',
                'Achieved 75% automation rate',
                'Created 40+ passing tests',
                'Deployed to production on Heroku',
            ],
            'skills_demonstrated': [
                'AI/ML Implementation (Classification, Pattern Recognition)',
                'Django Backend Development',
                'PostgreSQL Database Design',
                'Service-Oriented Architecture',
                'Test-Driven Development',
                'Deployment & DevOps',
            ],
            'leadership': [
                'Designed complete system architecture',
                'Created comprehensive documentation',
                'Managed end-to-end project lifecycle',
            ],
            'timeline': [
                {
                    'phase': 'Phase 1: Data Analysis',
                    'duration': '3 days',
                    'deliverables': [
                        'Analyzed $1.49M in transactions',
                        'Identified patterns and variances',
                        'Created tier classification algorithm',
                    ],
                },
                {
                    'phase': 'Phase 2: Implementation',
                    'duration': '5 days',
                    'deliverables': [
                        'Built SmartApprovalService',
                        'Created tier management UI',
                        'Integrated with budget workflow',
                    ],
                },
                {
                    'phase': 'Phase 3: Testing & Deployment',
                    'duration': '4 days',
                    'deliverables': [
                        'Created 40 comprehensive tests',
                        'Deployed to UAT and production',
                        'Documented system completely',
                    ],
                },
            ],
            'impact_metrics': {
                'time_saved': '10-15 hours/month',
                'cost_reduced': '$50K+ annually',
                'accuracy': '95%+',
                'user_satisfaction': 'Finance team loves auto-approval',
            },
        }

# Register the service
ProjectRegistry.register('budget-tier', BudgetTierPresentationService)
```

## Usage in Views

### Simple Usage

```python
from portfolio.services.base_presentation import ProjectRegistry

def project_presentation(request, project_slug, audience_type):
    """Render a project presentation for a specific audience"""
    
    # Get the service
    service = ProjectRegistry.get_service(project_slug)
    if not service:
        raise Http404("Project not found")
    
    # Determine presentation mode from URL
    presentation_mode = 'interview' if 'interview' in request.resolver_match.namespace else 'branded'
    
    # Get context
    context = service.get_context(audience_type, presentation_mode)
    
    # Render template
    template = f'portfolio/{project_slug}/{audience_type}.html'
    return render(request, template, context)
```

## Best Practices

### 1. Keep Services Focused
- Services handle **data generation only**
- No HTML rendering in services
- Return structured dicts, not strings

### 2. Use Consistent Keys
- Follow base context structure
- Use snake_case for keys
- Return lists/dicts, not primitives

### 3. Make Data Testable
```python
def test_investor_context():
    service = BudgetTierPresentationService()
    context = service.get_investor_context()
    
    assert 'market_size' in context
    assert 'roi_scenarios' in context
    assert len(context['roi_scenarios']) > 0
```

### 4. Document Data Shapes
```python
def get_roi_scenarios(self):
    """
    Returns list of ROI scenarios for investor pitch.
    
    Returns:
        list[dict]: Each dict has keys:
            - size: str (e.g., "Small Org")
            - investment: str (e.g., "$1,188/year")
            - savings: str (e.g., "$3,800/year")
            - roi: str (e.g., "320%")
            - payback_months: int
    """
```

## Adding New Services

1. **Create Service File**
   ```
   coda/portfolio/services/my_project_presentation.py
   ```

2. **Implement Service Class**
   ```python
   from .base_presentation import BasePresentationService, ProjectRegistry
   
   class MyProjectPresentationService(BasePresentationService):
       project_name = "My Project"
       project_slug = "my-project"
       # ... implement required methods
   
   ProjectRegistry.register('my-project', MyProjectPresentationService)
   ```

3. **Import in `__init__.py`**
   ```python
   # portfolio/services/__init__.py
   from .my_project_presentation import MyProjectPresentationService
   ```

4. **Create Templates**
   ```
   portfolio/templates/portfolio/my-project/
   ├── investor.html
   ├── technical.html
   └── recruiter.html
   ```

5. **Test**
   ```
   /portfolio/my-project/investor/
   /interview/my-project/technical/
   ```

## Troubleshooting

### Service Not Found
- Check `ProjectRegistry.register()` is called
- Verify import in `services/__init__.py`
- Confirm slug matches URL

### Missing Context Keys
- Ensure all required methods are implemented
- Check return type (should be dict)
- Verify keys match template expectations

### Wrong Branding
- Check URL namespace (`portfolio` vs `interview`)
- Verify `presentation_mode` is passed correctly
- Review `_get_branding()` logic

---

**See Also:**
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Complete system overview
- [../Presentations/ADDING_NEW_PROJECTS.md](../Presentations/ADDING_NEW_PROJECTS.md) - Step-by-step guide
- [../Testing/TESTING_GUIDE.md](../Testing/TESTING_GUIDE.md) - Testing services

**Last Updated:** October 16, 2025

