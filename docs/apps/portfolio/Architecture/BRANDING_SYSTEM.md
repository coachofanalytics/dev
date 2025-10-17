# Portfolio Branding System

**Last Updated:** October 16, 2025

## Overview

The portfolio app supports two distinct branding modes:
1. **Branded Mode** - Shows CODA company branding (for investor pitches, company presentations)
2. **Interview Mode** - White-label, personal branding only (for job applications, technical interviews)

## Branding Mode Detection

### Automatic Detection via URL

The branding mode is automatically determined by the URL path:

```python
# In views.py
def audience_specific_presentation(request, project_slug, audience):
    # Check URL namespace
    namespace = request.resolver_match.namespace
    
    # Determine mode
    if namespace == 'portfolio':
        presentation_mode = 'branded'    # Shows CODA branding
    elif namespace == 'interview':
        presentation_mode = 'interview'  # White-label
    else:
        presentation_mode = 'branded'    # Default
    
    # Pass to service
    context = service.get_context(audience, presentation_mode)
```

### URL Mapping

```
/portfolio/* → Branded Mode (CODA)
/interview/* → Interview Mode (White-label)
```

**Examples:**
```
https://codamakutano.herokuapp.com/portfolio/budget-tier/investor/
→ presentation_mode = 'branded'
→ Shows CODA logo, company info, corporate footer

https://codamakutano.herokuapp.com/interview/budget-tier/technical/
→ presentation_mode = 'interview'
→ Shows personal branding, your name, LinkedIn/GitHub
```

## Branding Context Variables

### Base Context (All Presentations)

```python
context = {
    'presentation_mode': 'branded' or 'interview',
    'show_branding': True or False,
    'branding': {
        # See detailed structure below
    },
    'project_name': 'Budget Tier System',
    'audience_type': 'investor',
    # ... other context
}
```

### Branded Mode Context

```python
'branding': {
    'mode': 'branded',
    'company_name': 'CODA Analytics',
    'logo_url': '/static/images/coda-logo.png',
    'tagline': 'Data-Driven Solutions',
    'website': 'https://coda.com',
    'contact': {
        'email': 'info@coda.com',
        'phone': '+254 XXX XXX XXX',
        'address': 'Nairobi, Kenya',
    },
    'social': {
        'linkedin': 'https://linkedin.com/company/coda',
        'twitter': 'https://twitter.com/coda',
    },
    'footer_text': '© 2025 CODA Analytics. All rights reserved.',
}
```

### Interview Mode Context

```python
'branding': {
    'mode': 'interview',
    'developer_name': 'Your Full Name',
    'developer_title': 'Full-Stack AI/ML Engineer',
    'logo_url': '/static/images/portfolio-logo.png',  # Personal logo
    'tagline': 'Building AI-Driven Solutions',
    'contact': {
        'email': 'your.email@example.com',
        'linkedin': 'https://linkedin.com/in/yourprofile',
        'github': 'https://github.com/yourprofile',
        'portfolio': 'https://yourportfolio.com',
    },
    'footer_text': 'Portfolio Project - October 2025',
}
```

## Template Implementation

### Base Template (shared/base_presentation.html)

```django
<!DOCTYPE html>
<html lang="en">
<head>
    <title>
        {% if show_branding %}
            CODA - {{ project_name }}
        {% else %}
            {{ project_name }} - {{ branding.developer_name }}
        {% endif %}
    </title>
</head>
<body class="{% if not show_branding %}interview-mode{% endif %}">
    
    {# Header with conditional branding #}
    <header class="presentation-header">
        {% if show_branding %}
            {# CODA Branded Header #}
            <div class="brand-header">
                <img src="{{ branding.logo_url }}" alt="CODA Logo" class="logo">
                <div class="brand-info">
                    <h1>{{ branding.company_name }}</h1>
                    <p class="tagline">{{ branding.tagline }}</p>
                </div>
            </div>
        {% else %}
            {# Personal/Interview Header #}
            <div class="personal-header">
                <div class="developer-info">
                    <h1>{{ project_name }}</h1>
                    <p class="byline">by <strong>{{ branding.developer_name }}</strong></p>
                    <p class="title">{{ branding.developer_title }}</p>
                </div>
            </div>
        {% endif %}
    </header>
    
    {# Main content #}
    <main>
        {% block content %}{% endblock %}
    </main>
    
    {# Footer with conditional contact info #}
    <footer class="presentation-footer">
        {% if show_branding %}
            {# Company Footer #}
            <div class="company-footer">
                <p>{{ branding.footer_text }}</p>
                <div class="contact-info">
                    <span><i class="fas fa-envelope"></i> {{ branding.contact.email }}</span>
                    <span><i class="fas fa-phone"></i> {{ branding.contact.phone }}</span>
                </div>
                <div class="social-links">
                    <a href="{{ branding.social.linkedin }}"><i class="fab fa-linkedin"></i></a>
                    <a href="{{ branding.social.twitter }}"><i class="fab fa-twitter"></i></a>
                </div>
            </div>
        {% else %}
            {# Personal Footer #}
            <div class="personal-footer">
                <p>{{ branding.footer_text }}</p>
                <div class="contact-links">
                    <a href="mailto:{{ branding.contact.email }}" title="Email">
                        <i class="fas fa-envelope"></i> Email
                    </a>
                    <a href="{{ branding.contact.linkedin }}" title="LinkedIn" target="_blank">
                        <i class="fab fa-linkedin"></i> LinkedIn
                    </a>
                    <a href="{{ branding.contact.github }}" title="GitHub" target="_blank">
                        <i class="fab fa-github"></i> GitHub
                    </a>
                </div>
            </div>
        {% endif %}
    </footer>
    
</body>
</html>
```

### Project-Specific Template

```django
{% extends "portfolio/shared/base_presentation.html" %}

{% block content %}
<section class="hero">
    <h2>{{ project_name }}</h2>
    
    {% if audience_type == 'investor' and show_branding %}
        {# Investor pitch - emphasize business value #}
        <p class="value-prop">Saving {{ metrics.annual_savings }} annually through AI automation</p>
        <p class="company-context">A CODA Analytics Solution</p>
        
    {% elif audience_type == 'technical' and not show_branding %}
        {# Technical interview - emphasize skills #}
        <p class="tech-stack">Built with Django, PostgreSQL, AI/ML</p>
        <p class="developer-context">Demonstrating full-stack AI/ML capabilities</p>
        
    {% endif %}
</section>

{# Rest of presentation content #}
{% endblock %}
```

## CSS Styling

### Branded Mode Styles

```css
/* Company branding colors */
.presentation-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: white;
}

.brand-header .logo {
    height: 60px;
    margin-right: 20px;
}

.brand-info h1 {
    font-size: 2rem;
    font-weight: bold;
    color: white;
}

.company-footer {
    background-color: #1e3a8a;
    color: white;
    padding: 2rem;
}
```

### Interview Mode Styles

```css
/* White-label / Personal branding */
body.interview-mode .presentation-header {
    background: linear-gradient(135deg, #475569 0%, #64748b 100%);
    color: white;
}

.personal-header .developer-info {
    text-align: center;
}

.personal-header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

.byline {
    font-size: 1.2rem;
    font-weight: 300;
}

.title {
    font-size: 1rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.personal-footer {
    background-color: #475569;
    color: white;
    padding: 2rem;
}

.contact-links a {
    display: inline-block;
    margin: 0 1rem;
    color: white;
    text-decoration: none;
    transition: color 0.3s;
}

.contact-links a:hover {
    color: #60a5fa;
}
```

## Configuration Settings

### Django Settings (base_settings.py)

```python
# Company Branding (for /portfolio/ URLs)
COMPANY_NAME = "CODA Analytics"
COMPANY_TAGLINE = "Data-Driven Solutions"
COMPANY_LOGO = "images/coda-logo.png"
COMPANY_EMAIL = "info@coda.com"
COMPANY_PHONE = "+254 XXX XXX XXX"
COMPANY_ADDRESS = "Nairobi, Kenya"
COMPANY_WEBSITE = "https://coda.com"

# Personal Branding (for /interview/ URLs)
DEVELOPER_NAME = "Your Full Name"
DEVELOPER_TITLE = "Full-Stack AI/ML Engineer"
DEVELOPER_EMAIL = "your.email@example.com"
DEVELOPER_LINKEDIN = "https://linkedin.com/in/yourprofile"
DEVELOPER_GITHUB = "https://github.com/yourprofile"
DEVELOPER_PORTFOLIO = "https://yourportfolio.com"
DEVELOPER_LOGO = "images/portfolio-logo.png"  # Optional
```

### Using Settings in Service

```python
# portfolio/services/base_presentation.py
from django.conf import settings

class BasePresentationService:
    def _get_branding(self, mode):
        if mode == 'branded':
            return {
                'mode': 'branded',
                'company_name': settings.COMPANY_NAME,
                'logo_url': f'/static/{settings.COMPANY_LOGO}',
                'tagline': settings.COMPANY_TAGLINE,
                'contact': {
                    'email': settings.COMPANY_EMAIL,
                    'phone': settings.COMPANY_PHONE,
                },
                # ... more fields
            }
        else:  # interview mode
            return {
                'mode': 'interview',
                'developer_name': getattr(settings, 'DEVELOPER_NAME', 'Developer'),
                'developer_title': getattr(settings, 'DEVELOPER_TITLE', 'Full-Stack Engineer'),
                'logo_url': f'/static/{getattr(settings, "DEVELOPER_LOGO", "images/default-logo.png")}',
                'contact': {
                    'email': getattr(settings, 'DEVELOPER_EMAIL', ''),
                    'linkedin': getattr(settings, 'DEVELOPER_LINKEDIN', ''),
                    'github': getattr(settings, 'DEVELOPER_GITHUB', ''),
                },
                # ... more fields
            }
```

## Branding Use Cases

### 1. Job Application (Technical Interview)

**URL:** `/interview/budget-tier/technical/`

**Branding:**
- ✅ Your name prominently displayed
- ✅ Personal title/role
- ✅ LinkedIn and GitHub links
- ❌ No company logo
- ❌ No company contact info
- ❌ No "CODA" mentions

**Why:** Interviewer sees **your** skills and experience, not employer branding

### 2. Investor Pitch

**URL:** `/portfolio/budget-tier/investor/`

**Branding:**
- ✅ CODA logo and company name
- ✅ Company tagline
- ✅ Company contact information
- ✅ Professional corporate appearance
- ❌ No personal branding

**Why:** Investor sees established company, not freelancer

### 3. Recruiter Outreach

**URL:** Can use either mode:
- `/portfolio/budget-tier/recruiter/` - Shows company context
- `/interview/budget-tier/recruiter/` - Shows personal achievements

**Recommended:** Start with branded mode (shows company context), but include link to toggle

## Mode Switching

### Option 1: Separate URLs (Current Implementation)

Users simply use different URLs:
```
Branded: /portfolio/budget-tier/technical/
Interview: /interview/budget-tier/technical/
```

**Pros:** 
- Simple, clear separation
- Easy to share correct link
- No state management

**Cons:**
- Must remember two URLs
- Can't toggle mid-presentation

### Option 2: Toggle Button (Future Enhancement)

Add a toggle button in navigation:

```django
<div class="mode-toggle">
    {% if show_branding %}
        <a href="{% url 'interview:audience_presentation' project_slug audience %}" 
           class="btn btn-sm">
            <i class="fas fa-user"></i> Switch to Interview Mode
        </a>
    {% else %}
        <a href="{% url 'portfolio:audience_presentation' project_slug audience %}" 
           class="btn btn-sm">
            <i class="fas fa-building"></i> Switch to Branded Mode
        </a>
    {% endif %}
</div>
```

### Option 3: Query Parameter (Future Enhancement)

```
/portfolio/budget-tier/technical/?mode=interview
```

## Testing Branding

### Checklist

- [ ] `/portfolio/` shows CODA branding
- [ ] `/interview/` shows personal branding (no CODA)
- [ ] Logo changes between modes
- [ ] Contact info changes between modes
- [ ] Footer text changes between modes
- [ ] Page title changes between modes
- [ ] Social links appropriate for mode
- [ ] CSS classes applied correctly (`interview-mode`)

### Visual Comparison

**Branded Mode:**
```
┌─────────────────────────────────┐
│ [CODA Logo] CODA Analytics      │
│ Data-Driven Solutions           │
├─────────────────────────────────┤
│ Budget Tier System              │
│ ...content...                   │
├─────────────────────────────────┤
│ © 2025 CODA Analytics           │
│ info@coda.com | +254 XXX        │
└─────────────────────────────────┘
```

**Interview Mode:**
```
┌─────────────────────────────────┐
│ Budget Tier System              │
│ by Your Name                    │
│ Full-Stack AI/ML Engineer       │
├─────────────────────────────────┤
│ ...content...                   │
├─────────────────────────────────┤
│ Portfolio Project - Oct 2025    │
│ [Email] [LinkedIn] [GitHub]     │
└─────────────────────────────────┘
```

## Best Practices

1. **Always test both modes** when creating new presentations
2. **Use conditional rendering** for company-specific vs personal content
3. **Keep personal branding professional** (no informal language in interview mode)
4. **Maintain consistency** across all presentations in same mode
5. **Update settings** when personal info changes (email, LinkedIn, etc.)

---

**Related Documentation:**
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [URL Structure](URL_STRUCTURE.md)
- [Service Layer](SERVICE_LAYER.md)

