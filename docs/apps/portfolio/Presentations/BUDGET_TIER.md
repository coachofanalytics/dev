# Budget Tier System Presentations

**Project:** AI-Driven Budget Tier System  
**Slug:** `budget-tier`  
**Service:** `BudgetTierPresentationService`  
**Status:** ✅ Complete (All 3 audience modes)

## Overview

The Budget Tier System is CODA's flagship finance automation project that uses AI/ML to automatically classify and approve budget requests, saving organizations $50K+ annually while maintaining 95%+ accuracy.

## Live Presentations

### Branded Mode (CODA)

- **Landing Page:** https://codamakutano.herokuapp.com/portfolio/budget-tier/
- **Investor Pitch:** https://codamakutano.herokuapp.com/portfolio/budget-tier/investor/
- **Technical Demo:** https://codamakutano.herokuapp.com/portfolio/budget-tier/technical/
- **Recruiter View:** https://codamakutano.herokuapp.com/portfolio/budget-tier/recruiter/

### Interview Mode (White-Label)

- **Technical Demo:** https://codamakutano.herokuapp.com/interview/budget-tier/technical/
- **Any Mode:** https://codamakutano.herokuapp.com/interview/budget-tier/{audience}/

## Audience Modes

### 1. Investor Presentation

**URL:** `/portfolio/budget-tier/investor/`  
**Target Audience:** VCs, Angel Investors, Business Partners  
**Duration:** 10-15 minutes  
**Focus:** Business value, ROI, market opportunity

**Key Sections:**

1. **Problem Statement**
   - Manual budget approval is slow and inconsistent
   - Finance teams overwhelmed with routine requests
   - No data-driven categorization

2. **Solution Overview**
   - AI-powered automatic categorization
   - Smart approval routing
   - Finance manager control panel

3. **Market Opportunity**
   - $2.5B enterprise budget software market
   - Every mid-to-large organization needs this
   - High switching costs create moat

4. **Business Model**
   - SaaS pricing: $500-5,000/month based on org size
   - Implementation fees: $10K-50K
   - Annual support contracts

5. **ROI Scenarios**
   - Small Org (100 requests/month): 320% ROI
   - Mid-size (500 requests/month): 480% ROI
   - Enterprise (2000 requests/month): 600% ROI

6. **Traction & Proof**
   - Live in production at CODA
   - $1.49M in data processed
   - 75% automation rate achieved
   - $50K+ annual savings

7. **Competitive Advantage**
   - Data-driven tier system (not hardcoded rules)
   - Self-learning classification
   - Finance manager oversight

8. **Go-to-Market**
   - Target: Finance departments at 200+ employee orgs
   - Channel: Direct sales + partnerships
   - Timeline: 6 months to first paid customer

9. **Financial Projections**
   - Year 1: 10 customers, $200K ARR
   - Year 2: 50 customers, $1.2M ARR
   - Year 3: 150 customers, $4.5M ARR

10. **Ask**
    - Seeking: $500K seed round
    - Use: Product development, sales team, marketing
    - Timeline: 18-month runway

**Call to Action:**
- Schedule follow-up meeting
- Connect with finance decision-makers
- Trial deployment discussion

---

### 2. Technical Presentation

**URL:** `/interview/budget-tier/technical/` (interview mode)  
**Target Audience:** Engineering teams, technical interviewers, CTOs  
**Duration:** 15-20 minutes  
**Focus:** Architecture, code, AI/ML implementation

**Key Sections:**

1. **Technical Challenge**
   - Classify 1000+ budget categories into 3 tiers
   - Analyze $1.49M in historical data
   - Achieve 95%+ accuracy without manual rules

2. **Technology Stack**
   ```
   Backend: Django 4.x, Python 3.10+
   Database: PostgreSQL with optimized indexes
   AI/ML: Statistical analysis, pattern recognition
   Frontend: jQuery 3.6, Bootstrap
   Testing: Django TestCase, 40+ tests
   Deployment: Heroku, Git-based CI/CD
   ```

3. **System Architecture**
   ```
   Transaction Data (Source of Truth)
   ↓
   Tier Classification Service
   ├── Statistical analysis
   ├── Pattern recognition
   └── Variance calculation
   ↓
   Smart Approval Service
   ├── Tier-based routing
   ├── Auto-approval logic
   └── Finance manager override
   ↓
   Budget Request Workflow
   ```

4. **AI/ML Approach**
   - **Classification Algorithm:**
     - Analyze 12 months of transaction history per category
     - Calculate typical monthly amounts
     - Determine variance thresholds
     - Assign tier (A/B/C) based on spend patterns
   
   - **Auto-Approval Logic:**
     - Tier A: Auto-approve if within variance
     - Tier B: Manager approval if over threshold
     - Tier C: Always require approval
   
   - **Continuous Learning:**
     - Re-classify quarterly based on new data
     - Finance manager can override tiers
     - Pattern analysis adapts to org changes

5. **Code Samples**
   
   **Tier Classification:**
   ```python
   def classify_tier(self, category):
       transactions = Transaction.objects.filter(
           category=category,
           transaction_date__gte=twelve_months_ago
       ).aggregate(
           avg_amount=Avg('amount'),
           stddev=StdDev('amount'),
           total_count=Count('id')
       )
       
       if transactions['total_count'] < 3:
           return 'C'  # Insufficient data
       
       avg = transactions['avg_amount']
       variance = transactions['stddev'] / avg if avg > 0 else 0
       
       if avg >= 50000:
           return 'A'  # High-value, recurring
       elif variance < 0.2:
           return 'A'  # Predictable spending
       elif variance < 0.5:
           return 'B'  # Moderate variance
       else:
           return 'C'  # High variance, needs review
   ```
   
   **Auto-Approval Logic:**
   ```python
   def should_auto_approve(self, budget_request):
       category = budget_request.budget_category
       
       if not category.auto_approve_enabled:
           return False, "Auto-approval disabled"
       
       if category.approval_tier == 'A':
           if self._within_threshold(budget_request, category):
               return True, "Tier A - within threshold"
       
       return False, f"Requires approval: Tier {category.approval_tier}"
   ```

6. **Database Design**
   - Extended `BudgetCategory` model with tier fields
   - Efficient queries using `select_related`
   - Indexed columns for performance

7. **Testing Strategy**
   - 40+ comprehensive tests
   - Unit tests for classification logic
   - Integration tests for approval workflow
   - Edge case handling (insufficient data, outliers)

8. **Performance Metrics**
   - Classification: < 100ms per category
   - Auto-approval decision: < 50ms
   - Dashboard load: < 500ms for 1000+ categories
   - Database: Optimized queries, no N+1 problems

9. **Deployment & DevOps**
   - Heroku deployment via Git push
   - Environment-specific settings
   - Database migrations tested in UAT
   - Rollback procedure documented

10. **Future Technical Enhancements**
    - Machine learning models (scikit-learn)
    - Real-time anomaly detection
    - API for external integrations
    - Mobile app for approvals

**Technical Highlights for Interviews:**
- "I analyzed $1.49M in real transaction data to build the classification system"
- "Achieved 75% automation rate with 95%+ accuracy"
- "Built 40+ comprehensive tests covering edge cases"
- "Optimized PostgreSQL queries to handle 10K+ categories"

---

### 3. Recruiter/HR Presentation

**URL:** `/portfolio/budget-tier/recruiter/`  
**Target Audience:** Recruiters, HR, hiring managers  
**Duration:** 5-10 minutes  
**Focus:** Achievements, impact, skills demonstrated

**Key Sections:**

1. **Project Summary**
   - AI-driven budget approval automation
   - Developed in 6 weeks
   - Live in production, processing real transactions

2. **Measurable Impact**
   - 💰 **$50,000+ annual savings**
   - ⚡ **75% automation rate** (3 out of 4 requests auto-approved)
   - 🎯 **95%+ accuracy** in classification
   - ⏱️ **2-3 month payback period**
   - 📊 **$1.49M in data** processed

3. **Skills Demonstrated**
   
   **Technical Skills:**
   - Python/Django backend development
   - PostgreSQL database design & optimization
   - AI/ML algorithm implementation
   - RESTful API design
   - Automated testing (TDD)
   - Git version control
   
   **Business Skills:**
   - Requirements gathering from stakeholders
   - Data-driven decision making
   - ROI calculation and projection
   - User experience design
   - Technical documentation
   
   **Soft Skills:**
   - Problem-solving (classified 1000+ categories)
   - Project management (6-week timeline)
   - Stakeholder communication
   - Continuous improvement mindset

4. **Project Timeline**
   - Week 1-2: Data analysis & tier classification
   - Week 3-4: Smart approval service implementation
   - Week 5: Finance manager UI & controls
   - Week 6: Testing, documentation, deployment

5. **Challenges Overcome**
   - **Challenge:** Inconsistent historical data
   - **Solution:** Built data cleanup pipeline, achieved 95.6% categorization
   
   - **Challenge:** Edge cases in approval logic
   - **Solution:** Multi-tier approach with fallback to manual approval
   
   - **Challenge:** Finance team trust in automation
   - **Solution:** Manager override controls and detailed audit logs

6. **Leadership & Initiative**
   - Identified inefficiency in manual approval process
   - Proposed data-driven solution
   - Delivered working system in 6 weeks
   - Trained finance team on new workflow

7. **Relevant Experience**
   - Full-stack development
   - AI/ML implementation in production
   - Agile/iterative development
   - Cross-functional collaboration
   - Production deployment & maintenance

8. **Portfolio Context**
   - Part of larger CODA finance platform
   - Integrates with existing transaction system
   - Foundation for future automation projects

9. **References & Validation**
   - Live system: https://codamakutano.herokuapp.com
   - Technical deep-dive available
   - Code samples on request
   - Finance team testimonials available

10. **Why This Project Matters**
    - Demonstrates **end-to-end ownership**
    - Shows **business impact**, not just code
    - Proves ability to **ship to production**
    - Illustrates **data-driven approach**
    - Highlights **AI/ML practical experience**

**Key Talking Points:**
- "I built a system that saves $50K+ annually through AI automation"
- "Delivered in 6 weeks from concept to production"
- "95% accuracy with real-world data, not just test scenarios"
- "Designed for business users, not just engineers"

---

## Template Files

Located in: `coda/portfolio/templates/portfolio/budget-tier/`

```
budget-tier/
├── investor.html      # Business-focused presentation
├── technical.html     # Engineering deep-dive
└── recruiter.html     # Achievements & impact
```

Each template extends:
```django
{% extends "portfolio/shared/base_presentation.html" %}
```

## Service Implementation

**File:** `coda/portfolio/services/budget_tier_presentation.py`

```python
class BudgetTierPresentationService(BasePresentationService):
    project_name = "AI-Driven Budget Tier System"
    project_slug = "budget-tier"
    
    def get_investor_context(self):
        return {
            'market_size': '$2.5B',
            'roi_scenarios': [...],
            'financial_projections': [...],
        }
    
    def get_technical_context(self):
        return {
            'tech_stack': [...],
            'architecture': [...],
            'code_samples': [...],
        }
    
    def get_recruiter_context(self):
        return {
            'achievements': [...],
            'skills': [...],
            'impact_metrics': [...],
        }
```

## Usage Guidelines

### For Investor Pitches
```
Use: /portfolio/budget-tier/investor/
Tone: Business-focused, ROI-driven
Duration: 10-15 minutes
Follow-up: Schedule demo, discuss pricing
```

### For Technical Interviews
```
Use: /interview/budget-tier/technical/
Tone: Technical depth, code samples
Duration: 15-20 minutes
Follow-up: Code repository access, technical discussion
```

### For Recruiter Screening
```
Use: /portfolio/budget-tier/recruiter/
Tone: Achievement-focused, impact-driven
Duration: 5-10 minutes
Follow-up: Technical interview, reference checks
```

## Related Documentation

- [Adding New Projects](ADDING_NEW_PROJECTS.md) - Template for creating similar presentations
- [Audience Modes](../Features/AUDIENCE_MODES.md) - Understanding different presentation modes
- [Interview Mode](../Features/INTERVIEW_MODE.md) - White-label usage guide

---

**Status:** ✅ All presentations complete and deployed  
**Last Updated:** October 16, 2025  
**UAT Version:** v935

