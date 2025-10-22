# Portfolio URL Structure

**Last Updated:** October 16, 2025

## Overview

The portfolio app uses a hierarchical, RESTful URL structure that supports multiple projects, audience types, and branding modes.

## URL Patterns

### Portfolio Hub (Branded Mode)

```
/portfolio/                          # Main gallery - all projects
```

**Purpose:** Central hub showing all projects with CODA branding  
**Template:** `portfolio/hub/gallery.html`  
**View:** `portfolio_hub`  
**Context:** `show_branding=True`

### Interview Hub (White-Label Mode)

```
/interview/                          # Interview gallery - white-label
```

**Purpose:** Same as portfolio hub but without company branding  
**Template:** `portfolio/hub/interview_gallery.html`  
**View:** `interview_hub`  
**Context:** `show_branding=False`

### Project Landing Pages

```
/portfolio/{project-slug}/           # Project overview + audience selector
/interview/{project-slug}/           # Same, white-label mode
```

**Example:**
```
/portfolio/budget-tier/              # Budget Tier landing (branded)
/interview/budget-tier/              # Budget Tier landing (white-label)
```

**Purpose:** Show project overview and links to all audience-specific presentations  
**Template:** `portfolio/project_landing.html`  
**View:** `project_landing`

### Audience-Specific Presentations

```
/portfolio/{project-slug}/{audience}/     # Specific presentation (branded)
/interview/{project-slug}/{audience}/     # Specific presentation (white-label)
```

**Example:**
```
/portfolio/budget-tier/investor/          # Investor pitch (CODA branded)
/portfolio/budget-tier/technical/         # Technical demo (CODA branded)
/portfolio/budget-tier/recruiter/         # Recruiter view (CODA branded)

/interview/budget-tier/technical/         # Technical demo (white-label)
/interview/budget-tier/investor/          # Investor pitch (white-label)
```

**Purpose:** Show full presentation for specific audience  
**Template:** `portfolio/{project-slug}/{audience}.html`  
**View:** `audience_specific_presentation`

### Presentation Guide

```
/portfolio/guide/                         # Master presentation guide
/portfolio/guide/{project-slug}/          # Project-specific guide
```

**Purpose:** How-to guides and talking points  
**Template:** `portfolio/guide/master_guide.html`  
**View:** `presentation_guide`

## URL Configuration (urls.py)

```python
# coda/portfolio/urls.py
from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    # ========== HUB ROUTES ==========
    path('', views.portfolio_hub, name='hub'),
    
    # ========== PROJECT ROUTES ==========
    # Project landing page (audience selector)
    path('<slug:project_slug>/', views.project_landing, name='project_landing'),
    
    # Audience-specific presentations
    path('<slug:project_slug>/<str:audience>/', 
         views.audience_specific_presentation, 
         name='audience_presentation'),
    
    # ========== GUIDE ROUTES ==========
    path('guide/', views.presentation_guide, name='guide'),
    path('guide/<slug:project_slug>/', views.project_guide, name='project_guide'),
]
```

### Interview Mode URLs (Separate Namespace)

```python
# coda/coda_project/urls.py
urlpatterns = [
    # Portfolio (branded)
    path("portfolio/", include("portfolio.urls", namespace="portfolio")),
    
    # Interview mode (white-label) - same app, different namespace
    path("interview/", include("portfolio.urls", namespace="interview")),
]
```

## URL Parameters

### `project_slug`
- **Type:** Slug field
- **Format:** `kebab-case`
- **Examples:** `budget-tier`, `ai-diaspora`, `smart-loan`
- **Validation:** Must match a registered project in `ProjectRegistry`

### `audience`
- **Type:** String
- **Format:** `lowercase`
- **Valid Values:**
  - `investor` - Financial/business focus
  - `technical` - Technical/engineering focus
  - `recruiter` - Achievements/HR focus
  - `demo` - Interactive demonstration
  - `banking` - Banking partnership (AI Diaspora specific)
  - `hybrid` - Mixed audience (AI Diaspora specific)

## Branding Mode Detection

The view automatically detects branding mode based on the URL namespace:

```python
def audience_specific_presentation(request, project_slug, audience):
    # Auto-detect branding mode from URL
    presentation_mode = 'branded' if request.resolver_match.namespace == 'portfolio' else 'interview'
    
    # Get service instance
    service = ProjectRegistry.get_service(project_slug)
    
    # Get context with correct branding
    context = service.get_context(audience, presentation_mode)
```

## URL Naming Conventions

### Pattern Names
```python
# Hub
portfolio:hub                         # /portfolio/
interview:hub                         # /interview/

# Project landing
portfolio:project_landing             # /portfolio/{slug}/
interview:project_landing             # /interview/{slug}/

# Presentations
portfolio:audience_presentation       # /portfolio/{slug}/{audience}/
interview:audience_presentation       # /interview/{slug}/{audience}/

# Guide
portfolio:guide                       # /portfolio/guide/
portfolio:project_guide               # /portfolio/guide/{slug}/
```

### Template Usage
```django
{# Link to branded investor presentation #}
<a href="{% url 'portfolio:audience_presentation' project_slug='budget-tier' audience='investor' %}">
    Investor Pitch
</a>

{# Link to white-label technical presentation #}
<a href="{% url 'interview:audience_presentation' project_slug='budget-tier' audience='technical' %}">
    Technical Demo (Interview Mode)
</a>

{# Link to project landing #}
<a href="{% url 'portfolio:project_landing' project_slug='budget-tier' %}">
    Budget Tier Overview
</a>
```

## Backward Compatibility

### Old URL Redirects

```python
# coda/finance/urls.py
from django.views.generic import RedirectView

urlpatterns = [
    # Old Budget Tier presentation URL
    path('budget-tier-presentation/', 
         RedirectView.as_view(url='/portfolio/budget-tier/investor/', permanent=True),
         name='old_budget_tier_presentation'),
    
    # Old presentation guide URL
    path('budget-tier-presentation-guide/',
         RedirectView.as_view(url='/portfolio/guide/budget-tier/', permanent=True),
         name='old_presentation_guide'),
]
```

### Old AI Services URLs

```python
# coda/ai_services/urls.py (future)
urlpatterns = [
    # Old diaspora presentation URL
    path('presentation_dashboard/',
         RedirectView.as_view(url='/portfolio/ai-diaspora/', permanent=True),
         name='old_diaspora_presentation'),
]
```

## Query Parameters

### Mode Toggle (Optional Enhancement)

```
?mode=branded           # Force branded mode
?mode=interview         # Force interview mode
```

**Note:** Currently not implemented. Branding is controlled by URL path (`/portfolio/` vs `/interview/`)

### Future Enhancements

```
?fullscreen=true        # Open in fullscreen mode
?print=true            # Print-optimized view
?embed=true            # Embeddable version
?lang=en               # Language selection
```

## URL Best Practices

### 1. Use Named URLs
```python
# Good
reverse('portfolio:audience_presentation', kwargs={'project_slug': 'budget-tier', 'audience': 'investor'})

# Bad
'/portfolio/budget-tier/investor/'
```

### 2. Keep Slugs Consistent
```python
# Good
project_slug = 'budget-tier'    # Matches service registration
service_class.project_slug = 'budget-tier'

# Bad
url: 'budget_tier'
service: 'budgetTier'
```

### 3. Validate Audience Types
```python
VALID_AUDIENCES = ['investor', 'technical', 'recruiter', 'demo', 'banking', 'hybrid']

if audience not in VALID_AUDIENCES:
    return HttpResponseNotFound(f"Audience '{audience}' not supported")
```

### 4. Handle 404s Gracefully
```python
try:
    service = ProjectRegistry.get_service(project_slug)
except KeyError:
    return HttpResponseNotFound(f"Project '{project_slug}' not found")
```

## URL Examples by Use Case

### Job Application (Technical Interview)
```
Share: https://codamakutano.herokuapp.com/interview/budget-tier/technical/

Breakdown:
- Base: codamakutano.herokuapp.com
- Mode: /interview/ (white-label)
- Project: budget-tier
- Audience: technical
```

### Investor Pitch
```
Share: https://codamakutano.herokuapp.com/portfolio/budget-tier/investor/

Breakdown:
- Base: codamakutano.herokuapp.com
- Mode: /portfolio/ (branded)
- Project: budget-tier
- Audience: investor
```

### Recruiter Outreach
```
Share: https://codamakutano.herokuapp.com/portfolio/budget-tier/recruiter/

Breakdown:
- Base: codamakutano.herokuapp.com
- Mode: /portfolio/ (branded - shows company context)
- Project: budget-tier
- Audience: recruiter
```

### Portfolio Discovery
```
Share: https://codamakutano.herokuapp.com/portfolio/

Breakdown:
- Base: codamakutano.herokuapp.com
- Mode: /portfolio/ (branded)
- View: Gallery showing all projects
```

## URL Testing Checklist

- [ ] `/portfolio/` → 200 OK (hub loads)
- [ ] `/interview/` → 200 OK (interview hub loads)
- [ ] `/portfolio/budget-tier/` → 200 OK (project landing)
- [ ] `/portfolio/budget-tier/investor/` → 200 OK
- [ ] `/portfolio/budget-tier/technical/` → 200 OK
- [ ] `/portfolio/budget-tier/recruiter/` → 200 OK
- [ ] `/interview/budget-tier/technical/` → 200 OK
- [ ] `/portfolio/invalid-project/` → 404
- [ ] `/portfolio/budget-tier/invalid-audience/` → 404 or friendly error
- [ ] Old URLs redirect correctly

## Common Issues

### Issue: 404 on /interview/
**Cause:** URL namespace not configured in main urls.py  
**Fix:** Ensure both `portfolio` and `interview` namespaces are included

### Issue: Wrong branding showing
**Cause:** Namespace detection not working  
**Fix:** Check `request.resolver_match.namespace` in view

### Issue: Template not found
**Cause:** Template path doesn't match project_slug  
**Fix:** Verify template is in `portfolio/templates/portfolio/{project-slug}/{audience}.html`

---

**Related Documentation:**
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [Service Layer](SERVICE_LAYER.md)
- [Branding System](BRANDING_SYSTEM.md)

