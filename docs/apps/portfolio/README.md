# Portfolio App Documentation

**Last Updated:** October 16, 2025  
**Status:** ✅ Production Ready  
**App Location:** `coda/portfolio/`

## Overview

The Portfolio app is a unified presentation system that showcases CODA projects for multiple audiences (investors, technical interviews, recruiters) with support for both branded (CODA) and white-label (interview) modes.

## Documentation Structure

```
docs/apps/portfolio/
├── README.md                           # This file - Overview and navigation
├── Architecture/
│   ├── SYSTEM_ARCHITECTURE.md          # Complete technical architecture
│   ├── SERVICE_LAYER.md                # BasePresentationService and project services
│   ├── URL_STRUCTURE.md                # URL routing and patterns
│   └── BRANDING_SYSTEM.md              # Branded vs white-label modes
├── Features/
│   ├── PORTFOLIO_HUB.md                # Main gallery and navigation
│   ├── INTERVIEW_MODE.md               # White-label interview presentations
│   ├── AUDIENCE_MODES.md               # Investor, Technical, Recruiter modes
│   └── DASHBOARD_INTEGRATION.md        # Integration with unified_dashboard
├── Presentations/
│   ├── BUDGET_TIER.md                  # Budget Tier System presentations
│   ├── AI_DIASPORA.md                  # AI Diaspora platform (future)
│   ├── SMART_LOAN.md                   # Smart Loan system (future)
│   └── ADDING_NEW_PROJECTS.md          # Guide for adding new projects
├── Testing/
│   ├── TESTING_GUIDE.md                # How to test portfolio features
│   └── URL_VERIFICATION.md             # Checklist for URL testing
└── Planning/
    ├── IMPLEMENTATION_COMPLETE.md      # Phase 1 completion summary
    ├── FUTURE_ENHANCEMENTS.md          # Phase 2 & 3 roadmap
    └── VISUAL_MOCKUPS.md               # UI designs and wireframes
```

## Quick Links

### 🏗️ Architecture
- [Complete System Architecture](Architecture/SYSTEM_ARCHITECTURE.md) - Technical overview, file structure, data flow
- [Service Layer Design](Architecture/SERVICE_LAYER.md) - BasePresentationService pattern
- [URL Structure](Architecture/URL_STRUCTURE.md) - Routing patterns and conventions
- [Branding System](Architecture/BRANDING_SYSTEM.md) - Branded vs interview modes

### ✨ Features
- [Portfolio Hub](Features/PORTFOLIO_HUB.md) - Main gallery and discovery
- [Interview Mode](Features/INTERVIEW_MODE.md) - White-label presentations
- [Audience Modes](Features/AUDIENCE_MODES.md) - Investor, Technical, Recruiter
- [Dashboard Integration](Features/DASHBOARD_INTEGRATION.md) - Unified dashboard links

### 🎯 Presentations
- [Budget Tier System](Presentations/BUDGET_TIER.md) - AI-powered budget approval
- [AI Diaspora Platform](Presentations/AI_DIASPORA.md) - Remittance and identity
- [Smart Loan System](Presentations/SMART_LOAN.md) - IoT + Blockchain lending
- [Adding New Projects](Presentations/ADDING_NEW_PROJECTS.md) - Step-by-step guide

### 🧪 Testing
- [Testing Guide](Testing/TESTING_GUIDE.md) - Comprehensive testing procedures
- [URL Verification](Testing/URL_VERIFICATION.md) - Checklist for all URLs

### 📋 Planning
- [Implementation Complete](Planning/IMPLEMENTATION_COMPLETE.md) - Phase 1 summary
- [Future Enhancements](Planning/FUTURE_ENHANCEMENTS.md) - Roadmap for Phase 2 & 3
- [Visual Mockups](Planning/VISUAL_MOCKUPS.md) - UI designs and user journeys

## Key Concepts

### 1. Unified Structure
All presentations follow a consistent pattern:
```
/portfolio/{project}/{audience}/
/interview/{project}/{audience}/
```

### 2. Branding Modes
- **Branded Mode** (`/portfolio/`): Shows CODA branding, company info
- **Interview Mode** (`/interview/`): White-label, personal branding only

### 3. Audience Types
- **Investor**: ROI, market opportunity, financial projections
- **Technical**: Architecture, code samples, AI/ML implementation
- **Recruiter**: Achievements, impact, skills demonstrated
- **Demo**: Interactive demonstrations

### 4. Service-Based Architecture
```python
BasePresentationService (base class)
├── BudgetTierPresentationService
├── AIDiasporaPresentationService
└── SmartLoanPresentationService
```

## Live URLs (UAT)

### Portfolio Hub
- **Main Gallery**: https://codamakutano.herokuapp.com/portfolio/
- **Interview Gallery**: https://codamakutano.herokuapp.com/interview/

### Budget Tier System
- **Landing**: https://codamakutano.herokuapp.com/portfolio/budget-tier/
- **Investor**: https://codamakutano.herokuapp.com/portfolio/budget-tier/investor/
- **Technical**: https://codamakutano.herokuapp.com/portfolio/budget-tier/technical/
- **Recruiter**: https://codamakutano.herokuapp.com/portfolio/budget-tier/recruiter/
- **Interview Mode**: https://codamakutano.herokuapp.com/interview/budget-tier/technical/

## Development Workflow

### Adding a New Presentation

1. **Create Service** (`portfolio/services/`)
   ```python
   class NewProjectPresentationService(BasePresentationService):
       project_name = "Project Name"
       project_slug = "project-slug"
   ```

2. **Register Project**
   ```python
   ProjectRegistry.register('project-slug', NewProjectPresentationService)
   ```

3. **Create Templates** (`portfolio/templates/portfolio/project-slug/`)
   - `investor.html`
   - `technical.html`
   - `recruiter.html`

4. **Test URLs**
   - `/portfolio/project-slug/`
   - `/portfolio/project-slug/investor/`
   - `/interview/project-slug/technical/`

See [Adding New Projects](Presentations/ADDING_NEW_PROJECTS.md) for detailed guide.

## Common Use Cases

### Job Application
```
Share: https://codamakutano.herokuapp.com/interview/budget-tier/technical/
Shows: Your skills, code samples, architecture (no company branding)
```

### Investor Pitch
```
Share: https://codamakutano.herokuapp.com/portfolio/budget-tier/investor/
Shows: CODA branded, ROI, market opportunity, financial projections
```

### Recruiter Outreach
```
Share: https://codamakutano.herokuapp.com/portfolio/budget-tier/recruiter/
Shows: Achievements, impact, skills (with company context)
```

## Integration Points

### From Unified Dashboard
- Quick Action: "Portfolio & Presentations"
- Admin role: Access to full portfolio hub
- Direct link: `/portfolio/`

### From Finance App
- Redirects from old URLs:
  - `/finance/budget-tier-presentation/` → `/portfolio/budget-tier/investor/`

### From AI Services App
- Future integration for AI Diaspora presentations

## Best Practices

### 1. URL Conventions
- Use kebab-case for project slugs: `budget-tier`, `ai-diaspora`
- Use lowercase for audience types: `investor`, `technical`, `recruiter`
- Keep URLs RESTful and predictable

### 2. Template Organization
- One template per audience type
- Extend from `shared/base_presentation.html`
- Use consistent section structure

### 3. Service Implementation
- Implement all abstract methods from `BasePresentationService`
- Return structured data (dicts with clear keys)
- Keep business logic in services, not views

### 4. Branding Control
- Rely on URL path for branding (automatic)
- Use `presentation_mode` in templates for conditional rendering
- Test both `/portfolio/` and `/interview/` URLs

## Troubleshooting

### Portfolio page returns 500 error
- Check `DEBUG=True` on UAT for detailed error
- Verify service is registered in `ProjectRegistry`
- Check template path matches project slug

### Wrong branding showing
- Verify URL starts with correct prefix (`/portfolio/` or `/interview/`)
- Check `presentation_mode` context variable in view

### Template not found
- Ensure template is in `portfolio/templates/portfolio/{project-slug}/`
- Verify filename matches audience type
- Check template extends from base correctly

## Support & Contact

For questions or issues with the portfolio system:
1. Review this documentation first
2. Check [SYSTEM_ARCHITECTURE.md](Architecture/SYSTEM_ARCHITECTURE.md) for technical details
3. See [TESTING_GUIDE.md](Testing/TESTING_GUIDE.md) for verification steps
4. Refer to [IMPLEMENTATION_COMPLETE.md](Planning/IMPLEMENTATION_COMPLETE.md) for status

---

**App Status:** ✅ Production Ready  
**Version:** Deployed to UAT (v935)  
**Last Tested:** October 16, 2025

