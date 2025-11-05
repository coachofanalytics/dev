# MAIN APP DOCUMENTATION

**App:** `coda/main/`  
**Last Updated:** November 5, 2025  
**Status:** Active

---

## OVERVIEW

The **Main** app serves as the central hub for CODA's public-facing pages, including:
- Company information (About Us, Why CODA, Careers)
- Team member profiles and categorization
- Services showcase
- Contact forms
- General utilities and helpers

---

## 📚 DOCUMENTATION INDEX

### **About Us & Team System** (Complete)

1. **[ABOUT_AND_TEAM_PAGES.md](./ABOUT_AND_TEAM_PAGES.md)** ⭐ **COMPREHENSIVE**
   - **1,194 lines** - Complete technical documentation
   - All views, models, templates explained in detail
   - Point calculation system breakdown
   - AI description generation
   - Image management
   - Related features and utilities
   - **Start here for in-depth understanding**

2. **[TEAM_SYSTEM_QUICK_REFERENCE.md](./TEAM_SYSTEM_QUICK_REFERENCE.md)** ⚡ **QUICK START**
   - **600+ lines** - Quick reference guide
   - URL access points
   - Team categorization flow diagrams
   - Point calculation examples
   - Common tasks and troubleshooting
   - Testing checklist
   - **Start here for quick lookups**

3. **[TEAM_SYSTEM_ARCHITECTURE.md](./TEAM_SYSTEM_ARCHITECTURE.md)** 🏗️ **TECHNICAL DEEP DIVE**
   - **900+ lines** - System architecture diagrams
   - Data flow visualizations
   - Database relationships
   - Request/response cycle
   - Performance analysis
   - Security model
   - **Start here for architecture understanding**

---

## 🚀 QUICK START

### Access the About Us Page
```
https://codamakutano.herokuapp.com/about/
```

### Access Team Profiles
```
https://codamakutano.herokuapp.com/members/team_profiles
https://codamakutano.herokuapp.com/members/client_profiles
https://codamakutano.herokuapp.com/members/future_talents
https://codamakutano.herokuapp.com/members/board
```

### View the Code
```python
# Views
coda/main/views.py (lines 986-1017)  # about()
coda/main/views.py (lines 739-928)   # team()

# Templates
coda/main/templates/main/about.html
coda/main/templates/main/team_profiles.html
coda/main/templates/main/snippets_templates/cards/team_card.html

# Models
coda/accounts/models.py (lines 186+)    # UserProfile
coda/accounts/models.py (lines 796-826) # Team_Members
coda/main/models.py (lines 340-360)     # Assets
```

---

## 📊 SYSTEM OVERVIEW

### Team Categorization System

```
TEAM MEMBER
    ↓
CALCULATE POINTS (from 5 sources)
    ├─ Education (250-10,000)
    ├─ Task History (variable)
    ├─ Requirements (variable)
    ├─ Training (5-125)
    └─ Client Assessment (variable)
    ↓
TOTAL POINTS
    ↓
ASSIGN TO CATEGORY
    ├─ Elite Team (superuser)
    ├─ Lead Team (>8,000)
    ├─ Senior Analysts (7,000-8,000)
    ├─ Junior Analysts (6,000-7,000)
    ├─ Senior Trainee (5,000-6,000)
    ├─ Junior Trainee (4,000-5,000)
    └─ Elementary (<4,000)
    ↓
GENERATE AI DESCRIPTION (if missing)
    ↓
DISPLAY ON TEAM PAGE
```

---

## 🔑 KEY FEATURES

### ✅ Implemented
- [x] Dynamic team categorization based on performance
- [x] AI-generated professional descriptions (OpenAI)
- [x] Google Drive image integration with fallbacks
- [x] Responsive design with "Read More/Less" functionality
- [x] LinkedIn profile integration
- [x] Admin-only total points display
- [x] Multi-category team pages (team, clients, future talents, board)
- [x] Configurable thresholds via Editable model

### 🔄 In Progress
- [ ] Performance optimization (point caching)
- [ ] Individual team member detail pages
- [ ] Search/filter functionality
- [ ] Automated tests

### 📋 Planned
- [ ] CDN for image delivery
- [ ] Management command for point recalculation
- [ ] Audit logging for profile changes
- [ ] Team member achievements/badges

---

## 🗂️ FILE STRUCTURE

```
coda/main/
├── views.py                          # Main views
│   ├── about()                       # About Us page
│   ├── team()                        # Team profiles
│   └── generate_openai_description() # AI descriptions
├── models.py
│   ├── Assets                        # Image management
│   └── Testimonials                  # Client reviews
├── urls.py                           # URL routing
├── forms.py                          # Contact forms, etc.
├── utils.py                          # Helper functions
├── templates/main/
│   ├── about.html                    # About Us template
│   ├── team_profiles.html            # Team profiles wrapper
│   └── snippets_templates/
│       └── cards/
│           └── team_card.html        # Team member cards
└── static/main/
    ├── css/
    │   └── team_card.css             # Team card styling
    └── img/
        └── profile/                  # Static profile images
            ├── amanda.jpeg
            ├── chris.jpeg
            ├── profile.jpeg
            └── ...

coda/accounts/
├── models.py
│   ├── UserProfile                   # Team member profiles
│   └── Team_Members                  # Category descriptions
```

---

## 🎯 COMMON TASKS

### View Documentation
```bash
# Full technical details
cat docs/apps/main/ABOUT_AND_TEAM_PAGES.md

# Quick reference
cat docs/apps/main/TEAM_SYSTEM_QUICK_REFERENCE.md

# Architecture diagrams
cat docs/apps/main/TEAM_SYSTEM_ARCHITECTURE.md
```

### Update Team Thresholds
```python
1. Django Admin → ai_services → Editable
2. Find: 'team_profile_value_json'
3. Update JSON:
   {
       "lead_team": 8000,
       "support_team": 1000,
       "delta": 1000,
       "percentage": 10
   }
4. Save
```

### Add New Team Member
```python
1. Django Admin → Accounts → CustomerUser
2. Create user with category=2 (Employee)
3. UserProfile auto-created via signal
4. Fill in: position, education, linkedin
5. Upload image (auto-uploads to Google Drive)
6. Complete ClientAssessment for AI description
7. System auto-calculates points and category
```

### Regenerate AI Descriptions
```python
# Currently happens automatically on page load if missing
# TODO: Create management command for batch regeneration
```

---

## 📈 METRICS & ANALYTICS

### Current System Stats
- **Team Members:** ~20-30 active
- **Categories:** 8 (Elite, Lead, Senior Analysts, Junior Analysts, Senior Trainee, Junior Trainee, Elementary, Support)
- **Point Sources:** 5 (Education, Tasks, Requirements, Training, Assessment)
- **Point Range:** 0 - 20,000+ possible
- **AI Descriptions:** Generated on-demand via OpenAI
- **Images:** Google Drive + local fallbacks

### Performance Profile
- **Query Complexity:** 1 main query + 5 subqueries per member = ~100 queries for 20 members
- **Load Time:** 1-3s typical, 3-43s worst case (with AI generation)
- **Optimization Potential:** 99% query reduction via caching

---

## 🔐 SECURITY

### Public Access
- About Us page
- Team profiles pages
- Team member descriptions
- Profile images
- LinkedIn links

### Restricted Access
- Total points (admin/staff only)
- Profile editing (owner + superuser only)
- Personal data (email, ID, contacts)

### Recommendations
1. Remove `|safe` filter from descriptions (XSS risk)
2. Add rate limiting to AI generation
3. Implement audit logging
4. Add image virus scanning
5. Review Google Drive permissions

---

## 🧪 TESTING

### Manual Testing Checklist
```bash
# About Page
□ Navigate to /about/
□ Verify hero section loads
□ Check team member grid displays
□ Test responsive design

# Team Profiles
□ Navigate to /members/team_profiles
□ Verify all categories display
□ Check member cards render
□ Test "Read More/Less" buttons
□ Verify images load or fallback
□ Check LinkedIn links work
□ Confirm admin sees points
□ Confirm non-admin doesn't see points
□ Test edit profile link (authorized only)

# Point Calculation
□ Verify education points correct
□ Check task history aggregation
□ Verify requirement points
□ Check training calculation
□ Confirm client assessment included
□ Verify total categorizes correctly

# AI Descriptions
□ Check descriptions generate when missing
□ Verify descriptions save to database
□ Test with missing ClientAssessment
□ Check error handling
```

### Automated Testing
```bash
# TODO: Create test suite
pytest tests/test_main_team.py -v
```

---

## 🐛 TROUBLESHOOTING

### Team member not showing
1. Check `user.is_active = True`
2. Check `user.category = 2` (Employee)
3. Check `member.description` exists
4. Check `member.img_category = 'employee'` (for About page)

### Wrong team category
1. Run point calculation manually
2. Verify threshold values in Editable model
3. Check sub_category (0=Board, 2=Contractor)

### Image not loading
1. Verify Google Drive image_url valid
2. Check static fallback image exists
3. Verify name matches static filename
4. Check Google Drive permissions

### Description missing
1. Check ClientAssessment exists for user email
2. Verify OpenAI API key configured
3. Check logs for AI generation errors
4. Add manual description via admin if needed

---

## 🔗 RELATED DOCUMENTATION

### Finance App
- Budget system uses `performance_tier` for loan terms
- Transaction system links to team members

### Accounts App
- UserProfile model (central to team system)
- Authentication and permissions

### Management App
- TaskHistory provides points
- Requirement provides points
- Training provides points

### Professional Services App
- ClientAssessment provides points and AI input

### AI Services App
- Editable model stores thresholds
- AI description generation

---

## 📞 SUPPORT

### Questions?
1. Read the comprehensive docs: `ABOUT_AND_TEAM_PAGES.md`
2. Check quick reference: `TEAM_SYSTEM_QUICK_REFERENCE.md`
3. Review architecture: `TEAM_SYSTEM_ARCHITECTURE.md`
4. Search codebase for specific functionality
5. Contact development team

### Contributing
1. Read existing code and documentation
2. Follow Django best practices
3. Write tests for new features
4. Update documentation
5. Submit for review

---

## 📝 CHANGELOG

### November 5, 2025
- ✅ Created comprehensive documentation suite
  - ABOUT_AND_TEAM_PAGES.md (1,194 lines)
  - TEAM_SYSTEM_QUICK_REFERENCE.md (600+ lines)
  - TEAM_SYSTEM_ARCHITECTURE.md (900+ lines)
  - README.md (this file)
- ✅ Documented all views, models, templates
- ✅ Documented point calculation system
- ✅ Documented AI description generation
- ✅ Documented image management system
- ✅ Created flow diagrams and architecture visuals

### Previous Updates
- October 2025: Team categorization system implemented
- September 2025: AI description generation added
- August 2025: Google Drive image integration

---

## 🎓 LEARNING RESOURCES

### For New Developers
1. **Start here:** `TEAM_SYSTEM_QUICK_REFERENCE.md` - Get familiar with URLs and basic flow
2. **Then read:** `ABOUT_AND_TEAM_PAGES.md` - Understand implementation details
3. **Finally review:** `TEAM_SYSTEM_ARCHITECTURE.md` - Understand system design

### For Experienced Developers
1. **Architecture:** `TEAM_SYSTEM_ARCHITECTURE.md` - System design and data flow
2. **Reference:** `ABOUT_AND_TEAM_PAGES.md` - Implementation details
3. **Quick lookup:** `TEAM_SYSTEM_QUICK_REFERENCE.md` - Commands and examples

### For Product/Business Team
1. **Feature overview:** This README
2. **User experience:** `/about/` and `/members/team_profiles` pages
3. **Configuration:** Team threshold settings in Editable model

---

## 🚀 NEXT STEPS

### Performance Optimization
1. Add `total_points` field to UserProfile
2. Create management command for daily point recalculation
3. Implement page caching (1 hour TTL)
4. Move to CDN for images
5. Add database indexes

### Feature Enhancements
1. Individual team member detail pages
2. Search/filter by skills, position, points
3. Team member achievements/badges
4. Export team data (CSV/PDF)
5. Public API for team data

### Testing & Quality
1. Write unit tests for point calculation
2. Write integration tests for views
3. Add performance monitoring
4. Implement error tracking
5. Add audit logging

### Documentation
1. Add inline code comments
2. Create video walkthrough
3. Add API documentation (if public API created)
4. Create user guide for admins

---

**End of Main App Documentation**

*For the CODA Budget System, see: `docs/apps/finance/Budgeting/MASTER_REFERENCE.md`*  
*For deployment info, see: `docs/05_DEPLOYMENT/`*  
*For testing strategy, see: `docs/TESTING_STRATEGY.md`*

