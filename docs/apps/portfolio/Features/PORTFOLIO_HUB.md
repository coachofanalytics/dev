# Portfolio Hub

**Last Updated:** October 16, 2025  
**URL:** `/portfolio/`  
**Template:** `portfolio/hub/gallery.html`

## Overview

The Portfolio Hub is the central landing page that showcases all CODA projects in a professional gallery format. It serves as the main entry point for discovering and navigating to specific project presentations.

## Live URL

**UAT:** https://codamakutano.herokuapp.com/portfolio/

## Features

### 1. Project Gallery

Displays all registered projects in a card-based layout:

```
┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│  AI Diaspora Platform│  │  Smart Loan System   │  │  Budget Tier AI     │
│  ──────────────────  │  │  ──────────────────  │  │  ─────────────────  │
│  Remittance & ID     │  │  IoT + Blockchain    │  │  Budget Automation  │
│  $50B Market         │  │  AI Risk Scoring     │  │  $50K+ Savings      │
│  200M+ Users         │  │  Smart Contracts     │  │  75% Automation     │
│                      │  │                      │  │                     │
│  [View Project]      │  │  [View Project]      │  │  [View Project]     │
└──────────────────────┘  └──────────────────────┘  └─────────────────────┘
```

### 2. CODA Branding

- CODA logo and company name in header
- Professional corporate color scheme
- Company tagline and value proposition
- Links to company resources

### 3. Quick Navigation

- Direct links to each project landing page
- Access to interview mode (white-label)
- Link to presentation guide
- Link back to unified dashboard

### 4. Responsive Design

- **Desktop:** 3-column card grid
- **Tablet:** 2-column card grid
- **Mobile:** Single-column stacked cards

## Template Structure

### Main Container

```django
{% extends "portfolio/shared/base_presentation.html" %}

{% block content %}
<div class="portfolio-hub">
    {# Hero Section #}
    <section class="hero">
        <h1>CODA Professional Portfolio</h1>
        <p class="tagline">Data-Driven Solutions for Real-World Problems</p>
    </section>
    
    {# Mode Toggle #}
    <section class="mode-selector">
        <a href="{% url 'interview:hub' %}" class="btn btn-outline">
            <i class="fas fa-user-tie"></i> View Interview Mode (White-Label)
        </a>
    </section>
    
    {# Project Gallery #}
    <section class="project-gallery">
        <h2>Our Solutions</h2>
        <div class="project-grid">
            {% for project in projects %}
                {% include "portfolio/hub/components/project_card.html" %}
            {% endfor %}
        </div>
    </section>
    
    {# Call to Action #}
    <section class="cta">
        <h3>Interested in Learning More?</h3>
        <p>Contact us to see how CODA solutions can transform your organization</p>
        <a href="mailto:{{ branding.contact.email }}" class="btn btn-primary">
            Get in Touch
        </a>
    </section>
</div>
{% endblock %}
```

### Project Card Component

```django
{# portfolio/hub/components/project_card.html #}
<div class="project-card" data-project="{{ project.slug }}">
    <div class="card-header">
        <h3>{{ project.name }}</h3>
        <span class="project-category">{{ project.category }}</span>
    </div>
    
    <div class="card-body">
        <p class="project-description">{{ project.description }}</p>
        
        <div class="key-metrics">
            {% for metric in project.key_metrics %}
            <div class="metric">
                <span class="metric-value">{{ metric.value }}</span>
                <span class="metric-label">{{ metric.label }}</span>
            </div>
            {% endfor %}
        </div>
        
        <div class="tech-stack">
            {% for tech in project.technologies %}
            <span class="tech-badge">{{ tech }}</span>
            {% endfor %}
        </div>
    </div>
    
    <div class="card-footer">
        <a href="{% url 'portfolio:project_landing' project.slug %}" 
           class="btn btn-primary btn-block">
            View Project Details
        </a>
        
        <div class="quick-links">
            <a href="{% url 'portfolio:audience_presentation' project.slug 'investor' %}" 
               class="quick-link">
                <i class="fas fa-chart-line"></i> Investor
            </a>
            <a href="{% url 'portfolio:audience_presentation' project.slug 'technical' %}" 
               class="quick-link">
                <i class="fas fa-code"></i> Technical
            </a>
        </div>
    </div>
</div>
```

## View Implementation

```python
# portfolio/views.py
from .services.base_presentation import ProjectRegistry

def portfolio_hub(request):
    """Main portfolio hub - shows all projects with CODA branding"""
    
    # Get all registered projects
    projects = []
    for project_slug, service_class in ProjectRegistry._projects.items():
        service = service_class()
        
        # Get basic project info
        project_info = {
            'name': service.project_name,
            'slug': service.project_slug,
            'description': service.get_description(),
            'category': service.get_category(),
            'key_metrics': service.get_key_metrics_summary(),
            'technologies': service.get_technologies_list(),
            'icon': service.get_icon(),
        }
        projects.append(project_info)
    
    context = {
        'presentation_mode': 'branded',
        'show_branding': True,
        'branding': _get_company_branding(),
        'projects': projects,
        'page_title': 'CODA Professional Portfolio',
    }
    
    return render(request, 'portfolio/hub/gallery.html', context)
```

## Project Data Structure

Each project card displays:

### Budget Tier System
```python
{
    'name': 'AI-Driven Budget Tier System',
    'slug': 'budget-tier',
    'description': 'Automated budget approval using AI classification and pattern analysis',
    'category': 'Finance Automation',
    'key_metrics': [
        {'value': '$50K+', 'label': 'Annual Savings'},
        {'value': '75%', 'label': 'Automation Rate'},
        {'value': '95%+', 'label': 'Accuracy'},
    ],
    'technologies': ['Django', 'PostgreSQL', 'AI/ML', 'Python'],
    'icon': 'fas fa-layer-group',
}
```

### AI Diaspora Platform
```python
{
    'name': 'AI Diaspora Platform',
    'slug': 'ai-diaspora',
    'description': 'Digital identity and remittance platform for diaspora communities',
    'category': 'Fintech & Identity',
    'key_metrics': [
        {'value': '$50B', 'label': 'Market Size'},
        {'value': '200M+', 'label': 'Target Users'},
        {'value': '10+', 'label': 'Countries'},
    ],
    'technologies': ['Django', 'AI/ML', 'Blockchain', 'Real-time Analytics'],
    'icon': 'fas fa-globe-africa',
}
```

### Smart Loan System
```python
{
    'name': 'Smart Loan System',
    'slug': 'smart-loan',
    'description': 'IoT-enabled microfinance with blockchain and AI risk scoring',
    'category': 'Fintech & IoT',
    'key_metrics': [
        {'value': '90%', 'label': 'Approval Accuracy'},
        {'value': 'IoT', 'label': 'Device Integration'},
        {'value': 'Blockchain', 'label': 'Security'},
    ],
    'technologies': ['Django', 'IoT', 'Blockchain', 'AI Risk Models'],
    'icon': 'fas fa-network-wired',
}
```

## Styling

### Color Scheme (Branded)

```css
:root {
    --coda-primary: #1e3a8a;      /* Deep blue */
    --coda-secondary: #3b82f6;    /* Bright blue */
    --coda-accent: #60a5fa;       /* Light blue */
    --coda-dark: #1e293b;         /* Dark slate */
    --coda-light: #f8fafc;        /* Light gray */
}

.portfolio-hub {
    background: linear-gradient(to bottom, var(--coda-light) 0%, white 100%);
    min-height: 100vh;
}

.hero {
    background: linear-gradient(135deg, var(--coda-primary) 0%, var(--coda-secondary) 100%);
    color: white;
    padding: 4rem 2rem;
    text-align: center;
}

.project-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s, box-shadow 0.3s;
    overflow: hidden;
}

.project-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
}
```

### Responsive Grid

```css
.project-grid {
    display: grid;
    gap: 2rem;
    padding: 2rem;
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
    .project-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

/* Tablet: 2 columns */
@media (min-width: 640px) and (max-width: 1023px) {
    .project-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Mobile: 1 column */
@media (max-width: 639px) {
    .project-grid {
        grid-template-columns: 1fr;
    }
}
```

## Navigation

### Header Navigation

```django
<nav class="hub-navigation">
    <div class="nav-left">
        <a href="{% url 'unified_dashboard:dashboard' %}">
            <i class="fas fa-arrow-left"></i> Back to Dashboard
        </a>
    </div>
    
    <div class="nav-center">
        <h1>CODA Portfolio</h1>
    </div>
    
    <div class="nav-right">
        <a href="{% url 'portfolio:guide' %}" class="btn btn-sm">
            <i class="fas fa-book"></i> Presentation Guide
        </a>
    </div>
</nav>
```

### Footer Links

```django
<footer class="hub-footer">
    <div class="footer-content">
        <div class="footer-section">
            <h4>Quick Links</h4>
            <ul>
                <li><a href="{% url 'interview:hub' %}">Interview Mode</a></li>
                <li><a href="{% url 'portfolio:guide' %}">Presentation Guide</a></li>
                <li><a href="{% url 'unified_dashboard:dashboard' %}">Dashboard</a></li>
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>Projects</h4>
            <ul>
                {% for project in projects %}
                <li><a href="{% url 'portfolio:project_landing' project.slug %}">{{ project.name }}</a></li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="footer-section">
            <h4>Contact</h4>
            <p>{{ branding.contact.email }}</p>
            <p>{{ branding.contact.phone }}</p>
        </div>
    </div>
    
    <div class="footer-bottom">
        <p>{{ branding.footer_text }}</p>
    </div>
</footer>
```

## Integration Points

### From Unified Dashboard

```python
# unified_dashboard/views.py
quick_actions = [
    {
        'title': 'Portfolio & Presentations',
        'url': '/portfolio/',
        'icon': 'fas fa-briefcase',
        'description': 'View all project presentations',
    }
]
```

### To Project Landing Pages

Each project card links to its landing page:
```
/portfolio/ → /portfolio/budget-tier/
/portfolio/ → /portfolio/ai-diaspora/
/portfolio/ → /portfolio/smart-loan/
```

### To Interview Mode

Toggle button at top of page:
```
/portfolio/ → /interview/ (white-label version)
```

## User Experience

### Flow 1: Investor Discovery

1. Visit `/portfolio/`
2. See 3 professional project cards with key metrics
3. Click "Budget Tier System" → lands on `/portfolio/budget-tier/`
4. Choose "Investor" audience → see investor pitch

### Flow 2: Quick Access

1. Visit `/portfolio/`
2. See quick links on project cards
3. Click "Technical" on Budget Tier card
4. Immediately opens `/portfolio/budget-tier/technical/`

### Flow 3: Switch to Interview Mode

1. Visit `/portfolio/`
2. Click "View Interview Mode" button
3. Redirects to `/interview/`
4. Same projects, no company branding

## Analytics (Future Enhancement)

Track engagement on portfolio hub:

```python
# Track project card clicks
def track_project_view(request, project_slug):
    PortfolioAnalytics.objects.create(
        project=project_slug,
        action='card_click',
        source='portfolio_hub',
        timestamp=timezone.now(),
    )
```

## Testing Checklist

- [ ] `/portfolio/` loads successfully (200 OK)
- [ ] All project cards display correctly
- [ ] CODA branding visible (logo, company name)
- [ ] Project metrics showing correctly
- [ ] Technology badges rendering
- [ ] "View Project" buttons work
- [ ] Quick links (Investor, Technical) work
- [ ] "Interview Mode" button works
- [ ] Responsive design works on mobile
- [ ] Footer links functional
- [ ] Back to dashboard link works

## Common Issues

### Issue: Projects not showing
**Cause:** Projects not registered in `ProjectRegistry`  
**Fix:** Ensure `ProjectRegistry.register()` called for each project

### Issue: Metrics not displaying
**Cause:** Service method `get_key_metrics_summary()` not implemented  
**Fix:** Implement method in project service class

### Issue: Broken project links
**Cause:** Project slug mismatch  
**Fix:** Verify `project_slug` matches in service and URL

---

**Related Documentation:**
- [Interview Mode](INTERVIEW_MODE.md)
- [Audience Modes](AUDIENCE_MODES.md)
- [Dashboard Integration](DASHBOARD_INTEGRATION.md)

