# TEAM SYSTEM - Quick Reference Guide

**Last Updated:** November 5, 2025  
**For Full Details:** See `ABOUT_AND_TEAM_PAGES.md`

---

## 🚀 QUICK ACCESS

### URLs
```
/about/                    → Main About Us page
/members/team_profiles     → Internal team (categorized by performance)
/members/client_profiles   → Client showcase
/members/future_talents    → Junior team members
/members/board            → Board of Governors
```

### Key Views
- `views.about()` - Lines 986-1017 in `coda/main/views.py`
- `views.team()` - Lines 739-928 in `coda/main/views.py`

---

## 📊 TEAM CATEGORIZATION FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    NEW TEAM MEMBER                          │
│                  (UserProfile created)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              CALCULATE TOTAL POINTS                         │
│                                                             │
│  1. Education Points      (250 - 10,000)                   │
│  2. Task History Points   (sum of completed tasks)         │
│  3. Requirement Points    (sum of task hours)              │
│  4. Training Points       (5 - 125 per level)              │
│  5. Assessment Points     (from ClientAssessment)          │
│                                                             │
│  TOTAL = Sum of all above                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ASSIGN TO TEAM CATEGORY                        │
│                                                             │
│  Elite Team           → Superuser only (c_maghas)          │
│  Lead Team            → > 8,000 points                     │
│  Senior Analysts      → 7,000 - 8,000 points               │
│  Junior Analysts      → 6,000 - 7,000 points               │
│  Senior Trainee       → 5,000 - 6,000 points               │
│  Junior Trainee       → 4,000 - 5,000 points               │
│  Elementary           → < 4,000 points                     │
│  Support Team         → Contractors > 1,000 points         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           GENERATE AI DESCRIPTION (if missing)              │
│                                                             │
│  Input: Name, Experience, Top 2 IT Skills                  │
│  Output: Professional bio paragraph                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DISPLAY ON TEAM PAGE                           │
│                                                             │
│  - Profile image (Google Drive or fallback)                │
│  - Name and position                                       │
│  - Total points (admin only)                               │
│  - LinkedIn link (if available)                            │
│  - Description with Read More/Less                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧮 POINT CALCULATION EXAMPLES

### Example 1: Lead Team Member
```python
Education:           Master's Degree = 6,000 points
Task History:        60 tasks × 50   = 3,000 points
Requirements:        300 hours       = 300 points
Training:            Level 5         = 125 points
Client Assessment:                   = 2,000 points
─────────────────────────────────────────────────
TOTAL:                                11,425 points
→ CATEGORY: LEAD TEAM ✅
```

### Example 2: Junior Analyst
```python
Education:           Bachelor's      = 3,000 points
Task History:        40 tasks × 50   = 2,000 points
Requirements:        150 hours       = 150 points
Training:            Level 3         = 45 points
Client Assessment:                   = 1,000 points
─────────────────────────────────────────────────
TOTAL:                                6,195 points
→ CATEGORY: JUNIOR ANALYSTS ✅
```

### Example 3: Senior Trainee
```python
Education:           Some College    = 1,000 points
Task History:        30 tasks × 50   = 1,500 points
Requirements:        100 hours       = 100 points
Training:            Level 2         = 20 points
Client Assessment:                   = 2,500 points
─────────────────────────────────────────────────
TOTAL:                                5,120 points
→ CATEGORY: SENIOR TRAINEE ✅
```

---

## 📁 KEY MODELS

### UserProfile
```python
# Location: coda/accounts/models.py
position          → Job title
description       → AI-generated bio
education         → 1-5 (High School to Doctorate)
image             → Local file
image2            → Google Drive link (via Assets)
linkedin          → LinkedIn URL
performance_tier  → NEW, BRONZE, SILVER, GOLD, PLATINUM
staff_level       → JUNIOR, SENIOR, MANAGER, EXECUTIVE
```

### Team_Members
```python
# Location: coda/accounts/models.py
category          → "board", "analytics_team", "future_talent", etc.
title             → "Project Manager", etc.
description       → Category description text
```

### Assets
```python
# Location: coda/main/models.py
name              → Asset name
category          → Asset type
image_url         → Google Drive file ID
service_image     → Local image file
```

---

## 🎨 TEMPLATE STRUCTURE

### About Page (`about.html`)
```
├── Hero Section
│   ├── Company tagline
│   └── Service badges
├── Mission & Vision
│   ├── Mission statement
│   ├── Vision statement
│   └── Core values
├── Services Overview
│   ├── Financial Services card
│   ├── Professional Training card
│   └── AI Services card
├── Team Section
│   └── Grid of active employees (img_category='employee')
├── Statistics
│   ├── Clients Served
│   ├── Projects Completed
│   ├── Years Experience
│   └── Client Satisfaction
└── Call to Action
    ├── Get Started button
    └── Contact Us button
```

### Team Profiles Page (`team_profiles.html`)
```
For each team category:
├── Left Column (col-md-3)
│   ├── Category name
│   └── Category description
└── Right Column (col-md-9)
    └── For each team member:
        ├── Profile image (120x120px circle)
        ├── Name (First, Last)
        ├── Position
        ├── Total points (admin only)
        ├── LinkedIn link (if available)
        ├── Description
        │   ├── Truncated text (220 chars)
        │   ├── Read More button
        │   ├── Full text (hidden)
        │   └── Read Less button
        └── Edit Profile link (authorized only)
```

---

## 🖼️ IMAGE SYSTEM

### Image Priority
```
1. Google Drive image → {{ googledriveurl }}{{ member.img_url }}
2. Static profile image → /static/main/img/profile/{{ name }}.jpeg
3. Default image → /static/main/img/service-1.jpg
```

### Image Fallback JavaScript
```javascript
function handleImageError(img, name) {
    if (img.src.includes('/static/')) {
        img.src = "{% static 'main/img/service-1.jpg' %}"
    } else {
        img.src = "{% static 'main/img/profile/' %}" + name.toLowerCase() + ".jpeg"
    }
}
```

### Available Static Images
```
amanda.jpeg, brenda.jpeg, caroline.jpeg, ceo_profile_v1.png,
chris.jpeg, edwin.jpeg, erick.jpeg, hashim.jpeg, judy.jpeg,
kennedy.jpeg, prachi.jpeg, profile.jpeg, sylvia.jpeg, victor.jpeg
```

---

## 🤖 AI DESCRIPTION GENERATION

### Trigger Conditions
```python
# Only generate if description is missing
if not user_profile.description:
    user_profile.description = generate_openai_description(user_profile)
    user_profile.save()
```

### Input Data
```python
- first_name          (from ClientAssessment)
- experience          (it_exp from ClientAssessment)
- top_2_skills        (sorted by rating, top 2)
```

### Skills Evaluated
```
Non-IT Experience, IT Experience, Project Charter,
Requirements Analysis, Reporting, ETL, Database,
Testing, Deployment, Frontend, Backend
```

### Example Prompt
```
"Generate a description for John, a professional with 
5 years of experience in ETL, Database."
```

---

## 🔧 CONFIGURATION

### Team Thresholds (Editable Model)
```json
{
    "lead_team": 8000,
    "support_team": 1000,
    "delta": 1000,
    "percentage": 10
}
```

**Location:** `Editable.objects.filter(name='team_profile_value_json')`

### Google Drive Folder ID
```python
folder_id = "1qzO8GAa5jGRgFYsamGEmnrI_bHbJ6Zre"
```

**Location:** `UserProfileUpdateView.form_valid()`

---

## 🔒 PERMISSIONS

### View Permissions
```python
About Page           → Public
Team Profiles        → Public
Update Profile       → @login_required + (superuser OR own profile)
View Total Points    → is_admin OR is_superuser OR is_staff
```

### Edit Permissions
```python
if request.user.is_superuser:
    return True  # Can edit any profile

elif request.user == profile.user:
    return True  # Can edit own profile

else:
    return False
```

---

## 📈 PERFORMANCE NOTES

### Current Query Complexity
```
1 main query + 5 subqueries per team member:
- Education points (annotated)
- Task history points (aggregated)
- Requirement points (aggregated)
- Training points (annotated)
- Client assessment points (subquery)
```

### Optimization Opportunities
1. **Cache total_points** - Add field to UserProfile, update daily
2. **Pre-generate descriptions** - Background job instead of on-demand
3. **CDN for images** - Serve from CDN instead of Google Drive
4. **Paginate teams** - If > 50 members per category

---

## 🐛 TROUBLESHOOTING

### Issue: Team member not showing
**Check:**
1. `user.is_active = True`?
2. `user.category = 2` (Employee)?
3. `member.description` exists?
4. `member.img_category = 'employee'` (for About page)?

### Issue: Wrong team category
**Check:**
1. Run point calculation query
2. Verify threshold values in Editable model
3. Check sub_category (0=Board, 2=Contractor)

### Issue: Image not loading
**Check:**
1. Google Drive image_url valid?
2. Static fallback image exists?
3. Name matches static filename?
4. Image permissions in Google Drive?

### Issue: Description missing
**Check:**
1. ClientAssessment record exists for user email?
2. OpenAI API key configured?
3. AI generation errors in logs?
4. Manual description can be added via admin

---

## 🔄 RELATED SYSTEMS

### Dependencies
```
TaskHistory        → Points calculation
Requirement        → Points calculation
Training           → Points calculation
ClientAssessment   → Points + AI description input
Editable           → Team thresholds
Assets             → Image management
```

### Affects
```
Finance Loan Terms → Uses performance_tier field
KCC Membership     → Uses performance_tier field
Dashboard Access   → Uses staff_level field
```

---

## 📝 COMMON TASKS

### Add New Team Member
```python
1. Create CustomerUser (category=2 for Employee)
2. UserProfile auto-created via signal
3. Fill in position, education, linkedin
4. Upload profile image (auto-uploads to Google Drive)
5. Complete ClientAssessment for AI description
6. System calculates points and assigns category
```

### Update Team Thresholds
```python
1. Go to Admin → Editable
2. Find 'team_profile_value_json'
3. Update JSON values:
   - lead_team: minimum points for lead team
   - support_team: minimum for support team
   - delta: point reduction per tier
   - percentage: % reduction when delta exhausted
4. Save → Next page load will use new thresholds
```

### Recalculate Points
```python
# No management command yet - points calculated on page load
# To force recalculation: reload /members/team_profiles
# TODO: Create management command for batch recalculation
```

### Add Category Description
```python
1. Go to Admin → Team_Members
2. Create new record:
   - category: "analytics_team" (or other)
   - title: "Analytics Team"
   - description: "Description text..."
3. Save → Displays on left side of team page
```

---

## 📚 FILE LOCATIONS

### Views
- `coda/main/views.py` (lines 739-928) - `team()`
- `coda/main/views.py` (lines 986-1017) - `about()`
- `coda/main/views.py` (lines 705-736) - `generate_openai_description()`

### Templates
- `coda/main/templates/main/about.html`
- `coda/main/templates/main/team_profiles.html`
- `coda/main/templates/main/snippets_templates/cards/team_card.html`

### Models
- `coda/accounts/models.py` (lines 186+) - `UserProfile`
- `coda/accounts/models.py` (lines 796-826) - `Team_Members`
- `coda/main/models.py` (lines 340-360) - `Assets`
- `coda/main/models.py` (lines 317-337) - `Testimonials`

### Static Assets
- `coda/main/static/main/img/profile/` - Profile images
- `coda/main/static/main/css/team_card.css` - Team card styling

### URLs
- `coda/main/urls.py` (line 13) - `/about/`
- `coda/main/urls.py` (line 28) - `/members/<str:title>`

---

## ✅ TESTING CHECKLIST

### Manual Testing
- [ ] Navigate to `/about/` - page loads
- [ ] Team section shows active employees
- [ ] Navigate to `/members/team_profiles` - all categories display
- [ ] Click "Read More" on long description - expands
- [ ] Click "Read Less" - collapses
- [ ] Images load or show fallback
- [ ] LinkedIn links work (if present)
- [ ] Admin sees total points
- [ ] Non-admin doesn't see total points
- [ ] Edit profile link visible to authorized users only

### Edge Cases
- [ ] Team member with no description
- [ ] Team member with no image
- [ ] Team member with no LinkedIn
- [ ] Team member with 0 points
- [ ] Team member with > 20,000 points
- [ ] Category with 0 members
- [ ] Category with 50+ members

### Point Calculation
- [ ] Education points correct (250-10,000)
- [ ] Task history points aggregate correctly
- [ ] Requirement points aggregate correctly
- [ ] Training points calculate correctly (5-125)
- [ ] Client assessment points included
- [ ] Total categorizes member correctly

---

## 🎯 SUMMARY

**What:** Dynamic team display system with performance-based categorization  
**Where:** `/about/` and `/members/*`  
**How:** Points calculation → Category assignment → AI description → Display  
**Why:** Showcase team expertise and create transparent performance tiers

**Key Benefits:**
- ✅ Automated categorization based on real performance data
- ✅ AI-generated professional descriptions
- ✅ Responsive, modern design
- ✅ Google Drive integration for scalable image storage
- ✅ Transparent point system for internal motivation

**Next Steps:**
1. Add management command for point recalculation
2. Implement caching for performance
3. Create individual team member detail pages
4. Add search/filter functionality
5. Write automated tests

---

**For detailed technical information, see `ABOUT_AND_TEAM_PAGES.md`**

