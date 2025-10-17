# Interview Mode (White-Label)

**Last Updated:** October 16, 2025  
**URL:** `/interview/*`  
**Purpose:** White-label presentations for job applications and technical interviews

## Overview

Interview Mode is a white-label version of the portfolio system that removes all company branding and focuses on showcasing **your personal skills and achievements**. It's specifically designed for job applications, technical interviews, and professional networking where company affiliation should not be the focus.

## Live URLs

**UAT:**
- Interview Hub: https://codamakutano.herokuapp.com/interview/
- Technical Demo: https://codamakutano.herokuapp.com/interview/budget-tier/technical/

## Key Features

### 1. No Company Branding
- ❌ No CODA logo
- ❌ No company name
- ❌ No company contact information
- ❌ No corporate messaging
- ✅ Your name and title
- ✅ Personal professional branding
- ✅ Your contact info (LinkedIn, GitHub, email)

### 2. Skills-Focused Content
- Emphasizes **your** technical capabilities
- Highlights **your** problem-solving approach
- Showcases **your** code and architecture decisions
- Demonstrates **your** impact and achievements

### 3. Professional Presentation
- Clean, modern design
- Focus on substance over corporate polish
- Easy-to-navigate structure
- Print/screen-share friendly

## What Changes in Interview Mode

### Header Comparison

**Branded Mode (`/portfolio/`):**
```
┌────────────────────────────────────────┐
│ [CODA Logo] CODA Analytics             │
│ Data-Driven Solutions                  │
│                                        │
│ Budget Tier System                     │
│ A CODA Analytics Solution              │
└────────────────────────────────────────┘
```

**Interview Mode (`/interview/`):**
```
┌────────────────────────────────────────┐
│ Budget Tier System                     │
│ by Your Name                           │
│ Full-Stack AI/ML Engineer              │
│                                        │
│ Demonstrating: AI/ML, Django, System   │
│ Architecture, PostgreSQL Optimization  │
└────────────────────────────────────────┘
```

### Footer Comparison

**Branded Mode:**
```
┌────────────────────────────────────────┐
│ © 2025 CODA Analytics                  │
│ All rights reserved                    │
│                                        │
│ Contact: info@coda.com                 │
│ Phone: +254 XXX XXX XXX                │
└────────────────────────────────────────┘
```

**Interview Mode:**
```
┌────────────────────────────────────────┐
│ Portfolio Project - October 2025       │
│                                        │
│ [📧 Email] [💼 LinkedIn] [💻 GitHub]  │
└────────────────────────────────────────┘
```

### Content Focus Changes

**Investor Mode (`/portfolio/*/investor/`):**
- "CODA's Budget Tier System saves companies $50K+ annually"
- "Our AI-driven solution..."
- "Contact CODA for a demo"

**Interview Technical Mode (`/interview/*/technical/`):**
- "I built an AI-driven system that automates budget approvals"
- "My approach to solving the classification problem..."
- "View my code samples and test suite"

## Use Cases

### 1. Technical Interview (Most Common)

**Scenario:** You're interviewing for an AI/ML Engineer position

**What to Share:**
```
https://codamakutano.herokuapp.com/interview/budget-tier/technical/
```

**What They See:**
- Your name and title
- Technical stack you used (Django, PostgreSQL, AI/ML)
- Problem you solved (automating budget approvals)
- Your code architecture
- Your testing approach
- Your problem-solving methodology

**During Interview:**
- Screen-share the presentation
- Walk through your technical decisions
- Show code samples
- Discuss challenges you faced
- Explain your AI/ML approach

### 2. LinkedIn Profile/Portfolio Link

**Scenario:** Recruiter views your LinkedIn profile

**What to Add:**
```
Portfolio: https://codamakutano.herokuapp.com/interview/
```

**What They See:**
- Professional project gallery
- Your personal branding
- Links to detailed technical presentations
- No confusion about current employer

### 3. GitHub README

**Scenario:** Showcase projects on your GitHub profile

**What to Add:**
```markdown
## Live Demonstrations

View interactive presentations of my projects:
- [Budget Tier AI System](https://codamakutano.herokuapp.com/interview/budget-tier/technical/)
- [AI Diaspora Platform](https://codamakutano.herokuapp.com/interview/ai-diaspora/technical/)
```

### 4. Email to Hiring Manager

**Scenario:** Follow-up after initial contact

**Email Template:**
```
Hi [Name],

Thank you for considering my application for [Position].

I've prepared a technical presentation showcasing a recent project 
that demonstrates my AI/ML and full-stack development skills:

https://codamakutano.herokuapp.com/interview/budget-tier/technical/

Key highlights:
• AI-driven classification system with 95%+ accuracy
• Full-stack Django application handling $1.49M in data
• 40+ comprehensive tests, all passing
• Measurable business impact ($50K+ annual savings)

I'd welcome the opportunity to discuss this project and how 
my experience aligns with your team's needs.

Best regards,
[Your Name]
```

## Interview Hub Gallery

### Template Structure

```django
{% extends "portfolio/shared/base_presentation.html" %}

{% block content %}
<div class="interview-hub">
    {# Hero - Professional but personal #}
    <section class="hero">
        <h1>{{ branding.developer_name }}</h1>
        <h2 class="title">{{ branding.developer_title }}</h2>
        <p class="tagline">Full-Stack Projects Demonstrating AI/ML & System Design</p>
    </section>
    
    {# Professional Summary #}
    <section class="summary">
        <p class="elevator-pitch">
            I build AI-driven systems that solve real business problems with 
            measurable impact. These projects demonstrate end-to-end capabilities 
            from data analysis to production deployment.
        </p>
    </section>
    
    {# Project Gallery #}
    <section class="project-gallery">
        <h2>Select a Project to Present</h2>
        <div class="project-grid">
            {% for project in projects %}
                <div class="project-card">
                    <h3>{{ project.name }}</h3>
                    <p>{{ project.description }}</p>
                    
                    <div class="technologies">
                        <strong>Technologies:</strong>
                        {% for tech in project.technologies %}
                        <span class="tech-badge">{{ tech }}</span>
                        {% endfor %}
                    </div>
                    
                    <div class="skills-demonstrated">
                        <strong>Skills Demonstrated:</strong>
                        <ul>
                            {% for skill in project.key_skills %}
                            <li>{{ skill }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    
                    <a href="{% url 'interview:audience_presentation' project.slug 'technical' %}" 
                       class="btn btn-primary">
                        View Technical Presentation
                    </a>
                </div>
            {% endfor %}
        </div>
    </section>
    
    {# Contact #}
    <section class="contact">
        <h3>Let's Connect</h3>
        <div class="contact-links">
            <a href="mailto:{{ branding.contact.email }}" class="contact-link">
                <i class="fas fa-envelope"></i> Email
            </a>
            <a href="{{ branding.contact.linkedin }}" target="_blank" class="contact-link">
                <i class="fab fa-linkedin"></i> LinkedIn
            </a>
            <a href="{{ branding.contact.github }}" target="_blank" class="contact-link">
                <i class="fab fa-github"></i> GitHub
            </a>
        </div>
    </section>
</div>
{% endblock %}
```

## Technical Presentation Example

### Budget Tier - Technical Mode

**URL:** `/interview/budget-tier/technical/`

**Content Focus:**

1. **Problem Statement**
   - "Organizations need to automate budget approval workflows"
   - "Manual categorization is slow and inconsistent"

2. **My Solution**
   - "I designed an AI classification system using statistical analysis"
   - "Built on Django with PostgreSQL for production scale"

3. **Technical Implementation**
   ```
   • Data Analysis: Analyzed $1.49M in real transaction data
   • AI/ML: Statistical classification with 95%+ accuracy
   • Backend: Django ORM with optimized queries
   • Database: PostgreSQL with proper indexing
   • Testing: 40+ unit and integration tests
   ```

4. **Code Samples**
   - Smart approval service logic
   - Tier classification algorithm
   - Test suite examples

5. **Architecture**
   - System diagram
   - Data flow
   - Service layer design

6. **Impact & Results**
   - 75% automation rate
   - $50K+ annual savings
   - 2-3 month payback period
   - 95%+ accuracy maintained

7. **Challenges & Solutions**
   - "Challenge: Handling edge cases in classification"
   - "Solution: Multi-tier approach with fallback logic"

## Styling for Interview Mode

### Color Scheme (Professional Gray/Blue)

```css
:root {
    --interview-primary: #475569;      /* Slate gray */
    --interview-secondary: #64748b;    /* Light slate */
    --interview-accent: #60a5fa;       /* Blue accent */
    --interview-dark: #1e293b;         /* Dark slate */
    --interview-light: #f1f5f9;        /* Light gray */
}

body.interview-mode {
    background: var(--interview-light);
    color: var(--interview-dark);
}

.interview-hub .hero {
    background: linear-gradient(135deg, var(--interview-primary) 0%, var(--interview-secondary) 100%);
    color: white;
    padding: 3rem 2rem;
    text-align: center;
}

.interview-hub h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.interview-hub .title {
    font-size: 1.25rem;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--interview-accent);
}
```

## Best Practices for Interviews

### Before the Interview

1. **Test the Link**
   - Open in incognito/private window
   - Verify no company branding shows
   - Check mobile responsiveness
   - Test on interview device (if screen-sharing)

2. **Prepare Talking Points**
   - "I built this system to solve X problem"
   - "My approach was to Y"
   - "The technical challenge was Z"
   - "I achieved W measurable impact"

3. **Practice Navigation**
   - Know where code samples are
   - Know where architecture diagrams are
   - Practice smooth scrolling/transitions

### During the Interview

1. **Opening**
   - "Let me show you a recent project that demonstrates my AI/ML skills"
   - Share screen with presentation already open

2. **Walkthrough**
   - Start with problem statement
   - Show technical approach
   - Highlight code samples
   - Discuss challenges and solutions
   - End with measurable impact

3. **Engagement**
   - Pause for questions
   - Be ready to dig deeper into code
   - Discuss alternative approaches you considered

### After the Interview

1. **Follow-Up Email**
   - Include link again
   - Reference specific technical discussions
   - Offer to discuss other projects

2. **LinkedIn Connection**
   - Add link to your profile
   - Make it easy for them to review later

## Configuration

### Set Your Personal Information

In `base_settings.py`:

```python
# Personal Branding for Interview Mode
DEVELOPER_NAME = "John Doe"
DEVELOPER_TITLE = "Full-Stack AI/ML Engineer"
DEVELOPER_EMAIL = "john.doe@example.com"
DEVELOPER_LINKEDIN = "https://linkedin.com/in/johndoe"
DEVELOPER_GITHUB = "https://github.com/johndoe"
DEVELOPER_PORTFOLIO = "https://johndoe.dev"  # Optional
```

## Switching Between Modes

### From Branded to Interview

Add a toggle button:

```django
{% if show_branding %}
<div class="mode-toggle">
    <a href="{% url 'interview:audience_presentation' project_slug audience %}" 
       class="btn btn-outline">
        <i class="fas fa-user-tie"></i> View in Interview Mode
    </a>
    <p class="help-text">Remove company branding for job applications</p>
</div>
{% endif %}
```

### From Interview to Branded

```django
{% if not show_branding %}
<div class="mode-toggle">
    <a href="{% url 'portfolio:audience_presentation' project_slug audience %}" 
       class="btn btn-outline">
        <i class="fas fa-building"></i> View Company Version
    </a>
    <p class="help-text">See full company presentation</p>
</div>
{% endif %}
```

## Testing Checklist

- [ ] `/interview/` loads without company branding
- [ ] Personal name/title displays correctly
- [ ] LinkedIn/GitHub links work
- [ ] Project cards emphasize skills, not company
- [ ] Technical presentations focus on your work
- [ ] Footer shows personal contact info only
- [ ] No "CODA" or company references anywhere
- [ ] Professional appearance maintained
- [ ] Responsive on mobile

## Common Questions

**Q: Can I still mention the company?**  
A: Yes, as context. Say "I worked with CODA to build..." rather than "CODA's system..."

**Q: Should I use interview mode for all networking?**  
A: Not always. For LinkedIn/GitHub, yes. For client pitches, use branded mode.

**Q: Can I customize the personal branding?**  
A: Yes, update `DEVELOPER_*` settings in `base_settings.py`

---

**Related Documentation:**
- [Portfolio Hub](PORTFOLIO_HUB.md)
- [Branding System](../Architecture/BRANDING_SYSTEM.md)
- [Audience Modes](AUDIENCE_MODES.md)

