# Unified Presentation System Architecture

**Created:** October 2025  
**Purpose:** Centralized, professional presentation system for portfolio, job applications, and investor pitches

## 🎯 Current State Analysis

### Existing Presentations

1. **AI Services - Diaspora Platform** (`ai_services/`)
   - Location: `/ai_services/presentation_dashboard/?mode=investor|banking|hybrid`
   - Service: `PresentationService` (ai_services/presentation_service.py)
   - Templates: `ai_services/templates/ai_services/presentation_*.html`
   - Features: Multiple modes, analytics tracking

2. **Finance - Smart Loan System** (`finance/`)
   - Location: `/finance/presentation/`
   - View: `loan_system_presentation()` in views.py
   - Template: `finance/loan_system_presentation.html`
   - Focus: Investor pitch for IoT + Blockchain + AI lending

3. **Finance - Budget Tier System** (NEW)
   - Location: `/finance/budget-tier-presentation/?mode=investor|technical|recruiter`
   - Service: `BudgetTierPresentationService`
   - Templates: `finance/budgets/presentations/*.html`
   - Features: Multiple audience modes

### Issues with Current Setup

1. ❌ **Scattered URLs**: Different patterns across apps
2. ❌ **No Central Hub**: Users can't discover all presentations
3. ❌ **Duplicate Code**: Similar presentation logic in different apps
4. ❌ **CODA Branding**: Can't easily hide for job interviews
5. ❌ **Hard to Navigate**: No unified navigation between presentations

## 🏗️ Proposed Unified Architecture

### 1. URL Structure (Hierarchical & Organized)

```
PORTFOLIO HUB
/portfolio/                                    # Central gallery (all projects)

PROJECT PRESENTATIONS (Branded - for CODA/Investors)
/portfolio/ai-diaspora/                       # AI Diaspora project landing
├── /investor/                                # Investor pitch
├── /banking/                                 # Banking partnership pitch
├── /hybrid/                                  # Hybrid pitch
└── /demo/                                    # Live demo

/portfolio/smart-loan/                        # Smart Loan project landing
├── /investor/                                # Investor pitch
├── /technical/                               # Technical deep-dive
└── /demo/                                    # Live demo

/portfolio/budget-tier/                       # Budget Tier project landing
├── /investor/                                # Investor pitch
├── /technical/                               # Technical interview
├── /recruiter/                               # Recruiter/HR view
└── /demo/                                    # Live demo

INTERVIEW MODE (White-label - no CODA branding)
/interview/                                    # Interview portfolio hub (unbranded)
├── /ai-diaspora/technical/                   # Technical interview mode
├── /smart-loan/technical/                    # Technical interview mode
├── /budget-tier/technical/                   # Technical interview mode
└── /guide/                                   # Interview preparation guide

PRESENTATION GUIDE
/portfolio/guide/                             # Master presentation guide
```

### 2. File Structure (Unified & Modular)

```
coda/
├── portfolio/                                 # NEW: Unified presentation app
│   ├── __init__.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_presentation_service.py      # Base class for all presentations
│   │   ├── ai_diaspora_presentation.py       # AI Diaspora (reuses ai_services logic)
│   │   ├── smart_loan_presentation.py        # Smart Loan (migrated from finance)
│   │   ├── budget_tier_presentation.py       # Budget Tier (migrated from finance)
│   │   └── portfolio_analytics.py            # Track views, engagement
│   │
│   ├── views/
│   │   ├── __init__.py
│   │   ├── hub_views.py                      # Portfolio hub/gallery
│   │   ├── project_views.py                  # Individual project presentations
│   │   └── interview_views.py                # Interview mode (white-label)
│   │
│   ├── urls.py                                # All presentation URLs
│   │
│   ├── templates/portfolio/
│   │   ├── hub/
│   │   │   ├── gallery.html                  # Main portfolio gallery
│   │   │   ├── interview_hub.html            # Interview mode gallery
│   │   │   └── components/
│   │   │       ├── project_card.html
│   │   │       └── audience_selector.html
│   │   │
│   │   ├── shared/                            # Shared across all projects
│   │   │   ├── base_presentation.html        # Master base (branded)
│   │   │   ├── base_interview.html           # Master base (white-label)
│   │   │   ├── navigation.html
│   │   │   └── components/
│   │   │       ├── metrics_card.html
│   │   │       ├── code_sample.html
│   │   │       ├── timeline.html
│   │   │       └── roi_calculator.html
│   │   │
│   │   ├── ai_diaspora/                      # AI Diaspora presentations
│   │   │   ├── landing.html
│   │   │   ├── investor.html
│   │   │   ├── banking.html
│   │   │   ├── hybrid.html
│   │   │   └── technical.html
│   │   │
│   │   ├── smart_loan/                       # Smart Loan presentations
│   │   │   ├── landing.html
│   │   │   ├── investor.html
│   │   │   ├── technical.html
│   │   │   └── demo.html
│   │   │
│   │   ├── budget_tier/                      # Budget Tier presentations
│   │   │   ├── landing.html
│   │   │   ├── investor.html
│   │   │   ├── technical.html
│   │   │   ├── recruiter.html
│   │   │   └── demo.html
│   │   │
│   │   └── guide/
│   │       ├── master_guide.html             # Overall presentation guide
│   │       ├── interview_prep.html           # Interview preparation
│   │       └── project_guides/               # Project-specific guides
│   │
│   └── static/portfolio/
│       ├── css/
│       │   ├── presentation-base.css         # Base styles
│       │   ├── branded-theme.css             # CODA-branded styles
│       │   ├── interview-theme.css           # White-label styles
│       │   └── project-themes/               # Project-specific themes
│       │
│       ├── js/
│       │   ├── presentation-controls.js      # Fullscreen, navigation
│       │   ├── mode-switcher.js              # Switch between modes
│       │   ├── analytics.js                  # Track engagement
│       │   └── demo-interactions.js          # Interactive demos
│       │
│       └── images/
│           ├── portfolio/                    # Portfolio-level images
│           ├── ai-diaspora/                  # AI Diaspora screenshots
│           ├── smart-loan/                   # Smart Loan screenshots
│           └── budget-tier/                  # Budget Tier screenshots
│
├── ai_services/                              # Existing app (references portfolio)
│   └── presentation_service.py               # DEPRECATED: Use portfolio.services
│
└── finance/                                  # Existing app (references portfolio)
    └── views.py                              # loan_system_presentation() → redirects to portfolio
```

### 3. Branding Control (White-label for Interviews)

#### Base Context for All Presentations

```python
# portfolio/services/base_presentation_service.py
class BasePresentationService:
    def get_context(self, audience_type, mode='branded'):
        """
        mode: 'branded' (shows CODA) or 'interview' (hides CODA)
        """
        context = {
            'presentation_mode': mode,
            'show_branding': mode == 'branded',
            'company_name': 'CODA' if mode == 'branded' else 'Portfolio Project',
            'logo_url': self._get_logo(mode),
            'contact_info': self._get_contact(mode),
            # ... other context
        }
        return context
    
    def _get_logo(self, mode):
        if mode == 'branded':
            return '/static/images/coda-logo.png'
        else:
            return '/static/images/portfolio-logo.png'  # Generic/Your initials
    
    def _get_contact(self, mode):
        if mode == 'branded':
            return {
                'email': 'info@coda.com',
                'phone': '+254...',
                'company': 'CODA Analytics',
            }
        else:
            return {
                'email': 'your.email@gmail.com',  # Your personal email
                'linkedin': 'linkedin.com/in/yourprofile',
                'github': 'github.com/yourprofile',
            }
```

#### Template Conditional Rendering

```django
{# portfolio/templates/shared/base_presentation.html #}
<div class="presentation-header {% if not show_branding %}interview-mode{% endif %}">
    <div class="branding">
        {% if show_branding %}
            <img src="{{ logo_url }}" alt="CODA Logo">
            <h1>CODA - {{ project_name }}</h1>
        {% else %}
            {# White-label mode - your personal branding #}
            <h1>{{ project_name }}</h1>
            <p class="byline">By {{ developer_name }}</p>
        {% endif %}
    </div>
</div>

{# Footer #}
<footer>
    {% if show_branding %}
        <p>&copy; 2025 CODA Analytics. All rights reserved.</p>
        <p>Contact: {{ contact_info.email }}</p>
    {% else %}
        <p>Portfolio Project - {{ created_date }}</p>
        <div class="contact-links">
            <a href="mailto:{{ contact_info.email }}"><i class="fas fa-envelope"></i></a>
            <a href="{{ contact_info.linkedin }}"><i class="fab fa-linkedin"></i></a>
            <a href="{{ contact_info.github }}"><i class="fab fa-github"></i></a>
        </div>
    {% endif %}
</footer>
```

### 4. Navigation & Discovery

#### Portfolio Hub (Main Landing)

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 Professional Portfolio                                   │
│  [Branded Mode] [Interview Mode]  ← Mode toggle             │
└─────────────────────────────────────────────────────────────┘

MY PROJECTS

┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│  AI Diaspora Platform│  │  Smart Loan System   │  │  Budget Tier AI     │
│  ──────────────────  │  │  ──────────────────  │  │  ─────────────────  │
│  $50B Market         │  │  IoT + Blockchain    │  │  $50K+ Savings      │
│  200M+ Users         │  │  AI Risk Scoring     │  │  75% Automation     │
│                      │  │                      │  │                     │
│  [Investor Pitch]    │  │  [Investor Pitch]    │  │  [Investor Pitch]   │
│  [Banking Pitch]     │  │  [Technical Deep-Dive]│  │  [Technical Demo]   │
│  [Technical Demo]    │  │  [Live Demo]         │  │  [Recruiter View]   │
└──────────────────────┘  └──────────────────────┘  └─────────────────────┘

QUICK ACCESS FOR INTERVIEWS
┌─────────────────────────────────────────────────────────────┐
│  🎤 Interview Mode (White-label - No Company Branding)      │
│  [View All Technical Presentations] → Opens unbranded view  │
└─────────────────────────────────────────────────────────────┘
```

#### Interview Mode Hub (White-label)

```
┌─────────────────────────────────────────────────────────────┐
│  Technical Portfolio Showcase                                │
│  Professional Projects Demonstrating AI/ML & System Design   │
└─────────────────────────────────────────────────────────────┘

SELECT A PROJECT TO PRESENT

┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│  AI Diaspora Platform│  │  Smart Loan System   │  │  Budget Tier AI     │
│                      │  │                      │  │                     │
│  Technologies:       │  │  Technologies:       │  │  Technologies:      │
│  • Python/Django     │  │  • IoT Integration   │  │  • ML Algorithms    │
│  • AI/ML Models      │  │  • Blockchain        │  │  • Django ORM       │
│  • Real-time Analytics│  │  • AI Risk Models    │  │  • PostgreSQL       │
│                      │  │                      │  │                     │
│  [Technical Demo]    │  │  [Technical Demo]    │  │  [Technical Demo]   │
│  [View Code Samples] │  │  [View Architecture] │  │  [View Test Suite]  │
└──────────────────────┘  └──────────────────────┘  └─────────────────────┘

NO COMPANY BRANDING | FOCUS ON YOUR SKILLS
```

### 5. Unified Navigation Component

```django
{# portfolio/templates/shared/navigation.html #}
<nav class="presentation-nav">
    <div class="nav-left">
        <a href="{% url 'portfolio:hub' %}">
            {% if show_branding %}
                <img src="/static/images/coda-logo.png" alt="CODA">
            {% else %}
                <i class="fas fa-briefcase"></i> Portfolio
            {% endif %}
        </a>
    </div>
    
    <div class="nav-center">
        <div class="breadcrumb">
            <a href="{% url 'portfolio:hub' %}">Portfolio</a>
            <span>/</span>
            <a href="{% url 'portfolio:project_landing' project.slug %}">{{ project.name }}</a>
            <span>/</span>
            <span>{{ audience_type|title }}</span>
        </div>
    </div>
    
    <div class="nav-right">
        {# Mode Switcher #}
        <div class="mode-toggle">
            {% if show_branding %}
                <a href="?mode=interview" class="btn btn-sm btn-outline-light">
                    <i class="fas fa-user-tie"></i> Interview Mode
                </a>
            {% else %}
                <a href="?mode=branded" class="btn btn-sm btn-outline-light">
                    <i class="fas fa-building"></i> Branded Mode
                </a>
            {% endif %}
        </div>
        
        {# Audience Switcher #}
        <div class="audience-switcher dropdown">
            <button class="btn btn-sm btn-light dropdown-toggle">
                {{ audience_type|title }} <i class="fas fa-chevron-down"></i>
            </button>
            <div class="dropdown-menu">
                <a class="dropdown-item" href="{% url 'portfolio:project_presentation' project.slug 'investor' %}">
                    <i class="fas fa-chart-line"></i> Investor
                </a>
                <a class="dropdown-item" href="{% url 'portfolio:project_presentation' project.slug 'technical' %}">
                    <i class="fas fa-code"></i> Technical
                </a>
                {% if project.has_recruiter %}
                <a class="dropdown-item" href="{% url 'portfolio:project_presentation' project.slug 'recruiter' %}">
                    <i class="fas fa-user-tie"></i> Recruiter
                </a>
                {% endif %}
            </div>
        </div>
        
        {# Controls #}
        <button class="btn btn-sm btn-outline-light" onclick="toggleFullscreen()">
            <i class="fas fa-expand"></i>
        </button>
        <a href="{% url 'portfolio:guide' %}" class="btn btn-sm btn-outline-light">
            <i class="fas fa-book"></i> Guide
        </a>
    </div>
</nav>
```

### 6. URL Configuration (urls.py)

```python
# coda/portfolio/urls.py
from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # ========== PORTFOLIO HUB ==========
    path('', views.portfolio_hub, name='hub'),
    path('interview/', views.interview_hub, name='interview-hub'),  # White-label mode
    
    # ========== PROJECT PRESENTATIONS ==========
    # AI Diaspora
    path('ai-diaspora/', views.project_landing, {'project': 'ai-diaspora'}, name='ai-diaspora-landing'),
    path('ai-diaspora/<str:audience>/', views.project_presentation, {'project': 'ai-diaspora'}, name='ai-diaspora-presentation'),
    
    # Smart Loan
    path('smart-loan/', views.project_landing, {'project': 'smart-loan'}, name='smart-loan-landing'),
    path('smart-loan/<str:audience>/', views.project_presentation, {'project': 'smart-loan'}, name='smart-loan-presentation'),
    
    # Budget Tier
    path('budget-tier/', views.project_landing, {'project': 'budget-tier'}, name='budget-tier-landing'),
    path('budget-tier/<str:audience>/', views.project_presentation, {'project': 'budget-tier'}, name='budget-tier-presentation'),
    
    # ========== GENERIC ROUTES (for scalability) ==========
    path('<slug:project_slug>/', views.project_landing, name='project-landing'),
    path('<slug:project_slug>/<str:audience>/', views.project_presentation, name='project-presentation'),
    
    # ========== GUIDE & RESOURCES ==========
    path('guide/', views.presentation_guide, name='guide'),
    path('guide/<slug:project_slug>/', views.project_guide, name='project-guide'),
]

# Redirect old URLs to new structure
# In finance/urls.py
path('presentation/', RedirectView.as_view(url='/portfolio/smart-loan/investor/', permanent=True)),
path('budget-tier-presentation/', RedirectView.as_view(url='/portfolio/budget-tier/', permanent=True)),

# In ai_services/urls.py
path('presentation_dashboard/', RedirectView.as_view(url='/portfolio/ai-diaspora/', permanent=True)),
```

### 7. Service Layer Architecture

```python
# portfolio/services/base_presentation_service.py
class BasePresentationService:
    """Base service for all presentations"""
    
    project_name = "Override in subclass"
    project_slug = "override-in-subclass"
    
    def get_context(self, audience_type, presentation_mode='branded'):
        """Get unified context for presentations"""
        base_context = {
            'project_name': self.project_name,
            'project_slug': self.project_slug,
            'audience_type': audience_type,
            'presentation_mode': presentation_mode,
            'show_branding': presentation_mode == 'branded',
            'branding': self._get_branding(presentation_mode),
            'technologies': self.get_technologies(),
            'key_metrics': self.get_key_metrics(),
            'created_date': self.get_created_date(),
        }
        
        # Audience-specific context
        if audience_type == 'investor':
            base_context.update(self.get_investor_context())
        elif audience_type == 'technical':
            base_context.update(self.get_technical_context())
        elif audience_type == 'recruiter':
            base_context.update(self.get_recruiter_context())
        
        return base_context
    
    def _get_branding(self, mode):
        if mode == 'branded':
            return {
                'company_name': 'CODA Analytics',
                'logo_url': '/static/images/coda-logo.png',
                'tagline': 'Data-Driven Solutions',
                'contact': {
                    'email': 'info@coda.com',
                    'phone': '+254...',
                }
            }
        else:  # interview mode
            return {
                'developer_name': 'Your Name',  # From settings
                'logo_url': '/static/images/portfolio-logo.png',
                'tagline': 'Full-Stack AI/ML Engineer',
                'contact': {
                    'email': 'your.email@gmail.com',
                    'linkedin': 'linkedin.com/in/yourprofile',
                    'github': 'github.com/yourprofile',
                }
            }
    
    # Abstract methods (must implement in subclasses)
    def get_technologies(self):
        raise NotImplementedError
    
    def get_key_metrics(self):
        raise NotImplementedError
    
    def get_investor_context(self):
        raise NotImplementedError
    
    def get_technical_context(self):
        raise NotImplementedError


# portfolio/services/budget_tier_presentation.py
class BudgetTierPresentationService(BasePresentationService):
    """Budget Tier specific implementation"""
    
    project_name = "AI-Driven Budget Tier System"
    project_slug = "budget-tier"
    
    def get_technologies(self):
        return {
            'backend': ['Django', 'PostgreSQL', 'Python'],
            'ai_ml': ['Statistical Analysis', 'Time Series', 'Classification'],
            'frontend': ['jQuery', 'Bootstrap', 'AJAX'],
        }
    
    # ... implement other methods
```

## 🎨 UI Components (2 Formats to Review)

### Current UI Areas to Improve

**1. Finance Dashboard Menu:**
- Add "Portfolio" or "Presentations" link
- Make it prominent for easy access

**2. Main Navigation:**
- Add top-level "Portfolio" menu item
- Dropdown with quick access to presentations

### Proposed UI Improvements

#### Option A: Dedicated Portfolio Section in Main Nav
```
[Home] [Finance] [AI Services] [Portfolio ▼] [About]
                                    ├── All Projects
                                    ├── Interview Mode
                                    ├── AI Diaspora →
                                    ├── Smart Loan →
                                    └── Budget Tier →
```

#### Option B: Quick Access Widget
```
┌─────────────────────────────┐
│  🎯 Portfolio Presentations │
│  ─────────────────────────  │
│  [View All Projects]        │
│  [Interview Mode]           │
│  [Presentation Guide]       │
└─────────────────────────────┘
```

## 📋 Implementation Plan

### Phase 1: Foundation (Do First)
1. Create `portfolio/` app
2. Create base services and views
3. Set up URL structure
4. Create hub/gallery templates
5. Implement branding toggle

### Phase 2: Migration (Next)
1. Migrate Budget Tier presentation
2. Migrate Smart Loan presentation
3. Integrate AI Diaspora presentation
4. Update all redirects

### Phase 3: Enhancement (Later)
1. Add analytics tracking
2. Create comprehensive guide
3. PDF export functionality
4. Improve UI navigation

## 🚀 Benefits of This Architecture

1. ✅ **Centralized**: All presentations in one place
2. ✅ **Discoverable**: Portfolio hub makes everything easy to find
3. ✅ **White-label Ready**: Easy toggle for interview mode
4. ✅ **Scalable**: Easy to add new projects
5. ✅ **Maintainable**: Unified code, no duplication
6. ✅ **Professional**: Consistent UX across all presentations
7. ✅ **Flexible**: Support multiple audiences per project

---

**Next Steps**: Review and approve this architecture before implementation.

