# Team Assignment System - Requirements

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 📋 Requirements Defined

---

## 🎯 Business Requirements

### **BR-1: Team Structure Display**
**Priority:** P0 - Critical

**Requirement:**  
Display CODA team members organized by categories with accurate assignments.

**Team Structure:**

**Manual Categories (10 members):**
1. **BOG/Leadership** (3 members)
   - Amanda Towe
   - Chris Maghas (username: `cmaghas`)
   - Tirimba Obonyo

2. **Elite Team** (1 member)
   - Chris Maghas (username: `coda-info`)

3. **Lead Team** (3 members)
   - Edwin Kimtai
   - Emanuel Masakhwe
   - George Ndahiro

4. **Support Team** (2 members)
   - Hashim Kha
   - Christine Karagu

5. **Senior Analysts** (1 member)
   - Sylvia Jelante

6. **Junior Analysts** (1 member)
   - Phinehas Maina

**Points-Based Categories (4+ members):**
7. **Senior Trainee** (5,000-6,000 points)
   - Bonie Luke
   - Brenda Nasimiyu

8. **Junior Trainee** (4,000-5,000 points)
   - Angel
   - Eugene

9. **Elementary** (<4,000 points)
   - (Future new trainees)

---

### **BR-2: Manual Team Assignment**
**Priority:** P0 - Critical

**Requirement:**  
Admin must be able to manually assign team members to categories regardless of points.

**Acceptance Criteria:**
- ✅ Admin can assign via Django Admin
- ✅ Admin can assign via management command
- ✅ Manual assignment overrides points-based
- ✅ Can set priority/ordering within category
- ✅ Can track who assigned and when

---

### **BR-3: Automated Trainee Progression**
**Priority:** P1 - High

**Requirement:**  
Trainees automatically categorize by performance points.

**Acceptance Criteria:**
- ✅ Points calculated daily
- ✅ Auto-categorize: <4K → Elementary, 4-5K → Junior Trainee, 5-6K → Senior Trainee
- ✅ Auto-flag at 6,000+ points for promotion
- ✅ Clear progression visibility

---

### **BR-4: Performance Requirements**
**Priority:** P1 - High

**Requirement:**  
Team pages must load fast with minimal database queries.

**Acceptance Criteria:**
- ✅ Page load < 2 seconds
- ✅ < 10 database queries per page
- ✅ Points cached (not calculated on-demand)
- ✅ Page caching enabled

---

## 📊 Functional Requirements

### **FR-1: Django Groups Integration**
**Priority:** P0 - Critical

**Requirements:**
- ✅ Use Django's built-in Group model
- ✅ Create 9 team category groups
- ✅ Assign users to appropriate groups
- ✅ Query by group membership
- ✅ Support multiple group membership (if needed)

**Implementation:**
```python
from django.contrib.auth.models import Group

# Create groups
Group.objects.create(name='BOG/Leadership')
Group.objects.create(name='Elite Team')
# etc...

# Assign users
user.groups.add(group)

# Query
members = User.objects.filter(groups__name='Lead Team')
```

---

### **FR-2: TeamProfile Model**
**Priority:** P0 - Critical

**Requirements:**
- ✅ Create new TeamProfile model
- ✅ OneToOne relationship with User
- ✅ Store metadata only (not category - Groups handles that)
- ✅ Fields: priority, total_points, is_manually_assigned, last_promoted, promotion_notes
- ✅ Total: 5 fields only

**Model Design:**
```python
class TeamProfile(models.Model):
    user = OneToOneField(User, on_delete=CASCADE)
    priority = IntegerField(default=0, db_index=True)
    total_points = IntegerField(default=0, db_index=True)
    is_manually_assigned = BooleanField(default=False)
    last_promoted = DateTimeField(null=True)
    promotion_notes = TextField(blank=True)
    
    @property
    def category(self):
        """Get category from user's groups"""
        for cat in TEAM_GROUPS:
            if self.user.groups.filter(name=cat).exists():
                return cat
        return None
```

---

### **FR-3: Point Calculation System**
**Priority:** P1 - High

**Requirements:**
- ✅ Calculate points from 5 sources
- ✅ Cache in TeamProfile.total_points
- ✅ Recalculate daily via cron
- ✅ Only calculate for non-manual members
- ✅ Flag promotion candidates (≥6,000 points)

**Point Sources:**
1. **Education:** 250 - 10,000 points
2. **Task History:** Sum of task points
3. **Requirements:** Sum of task hours
4. **Training:** 5 - 125 points per level
5. **Client Assessment:** Variable

---

### **FR-4: Team Assignment Logic**
**Priority:** P0 - Critical

**Requirements:**
- ✅ Manual assignment for senior roles
- ✅ Points-based for trainees
- ✅ Manual takes precedence
- ✅ Clear assignment method

**Logic:**
```python
if user in manual_group:
    category = group.name  # Manual assignment
else:
    if points >= 5000:
        category = 'Senior Trainee'  # Auto
    elif points >= 4000:
        category = 'Junior Trainee'  # Auto
    else:
        category = 'Elementary'  # Auto
```

---

### **FR-5: Management Commands**
**Priority:** P0 - Critical

**Requirements:**
- ✅ `create_team_groups` - Create Django Groups
- ✅ `verify_team_members` - Check members exist
- ✅ `assign_manual_team_members` - Assign manual categories
- ✅ `recalculate_team_points` - Calculate points
- ✅ `show_promotion_candidates` - Show who's ready
- ✅ `promote_team_member` - Promote someone

---

### **FR-6: Team Display Pages**
**Priority:** P0 - Critical

**Requirements:**
- ✅ `/members/team_profiles` - Show manual categories
- ✅ `/members/future_talents` - Show points-based categories
- ✅ `/members/board` - Show BOG/Leadership
- ✅ Display by priority within category
- ✅ Show points (admin only)
- ✅ Show LinkedIn links
- ✅ Show descriptions with Read More/Less

---

### **FR-7: Admin Interface**
**Priority:** P1 - High

**Requirements:**
- ✅ Django Admin for TeamProfile
- ✅ List display: user, category, points, priority
- ✅ Filters: is_manually_assigned, category
- ✅ Bulk actions: promote, recalculate points
- ✅ Search: by username, email

---

## 🚀 Non-Functional Requirements

### **NFR-1: Performance**
**Priority:** P1 - High

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Queries/page | 100-120 | < 10 | 95% reduction |
| Load Time | 3-43s | < 2s | 85% faster |
| TTFB | 2-3s | < 500ms | 80% faster |
| Database Size | Large | Same | No bloat |

---

### **NFR-2: Scalability**
**Priority:** P2 - Medium

**Requirements:**
- ✅ Support 100+ team members
- ✅ Support 9 categories
- ✅ Daily point recalculation < 1 minute
- ✅ Page caching for high traffic

---

### **NFR-3: Maintainability**
**Priority:** P1 - High

**Requirements:**
- ✅ Clean code structure
- ✅ Comprehensive tests (80%+ coverage)
- ✅ Documentation
- ✅ No UserProfile bloat
- ✅ Single Responsibility Principle

---

### **NFR-4: Security**
**Priority:** P1 - High

**Requirements:**
- ✅ Group management: Admin only
- ✅ TeamProfile edits: Admin only
- ✅ Point viewing: Admin/Staff only
- ✅ Audit trail for promotions
- ✅ XSS protection (no |safe filters)

---

## 📊 User Stories

### **US-1: View Team by Category**
**As a** visitor  
**I want to** see team members organized by category  
**So that** I can understand the team structure

**Acceptance Criteria:**
- Team categories display in order
- Members within categories are sorted
- Images display correctly
- Descriptions show with Read More/Less

---

### **US-2: Manual Team Assignment**
**As an** admin  
**I want to** manually assign team members to categories  
**So that** I can control strategic roles

**Acceptance Criteria:**
- Can assign via Django Admin
- Can assign via management command
- Assignment saves correctly
- Display reflects assignment

---

### **US-3: Automated Trainee Progression**
**As a** trainee  
**I want to** automatically progress based on performance  
**So that** my advancement is transparent and fair

**Acceptance Criteria:**
- Points calculate daily
- Category updates automatically
- Can see current points (if logged in)
- Clear progression criteria

---

### **US-4: Promotion Review**
**As an** admin  
**I want to** see trainees ready for promotion  
**So that** I can review and promote deserving members

**Acceptance Criteria:**
- System flags members with 6,000+ points
- Shows point breakdown
- Can review and promote
- Promotion is tracked

---

## ✅ Acceptance Criteria Summary

### **Must Have (P0)**
- [x] Django Groups created for 9 categories
- [x] TeamProfile model created (5 fields)
- [x] Manual assignment works for 10 members
- [x] Points calculation works for trainees
- [x] Team pages display correctly
- [x] UserProfile stays at 38 fields
- [x] Page loads < 2 seconds

### **Should Have (P1)**
- [x] Promotion candidate detection
- [x] Admin interface configured
- [x] Management commands work
- [x] Caching implemented
- [x] Tests written (80%+ coverage)

### **Nice to Have (P2)**
- [ ] Individual member pages
- [ ] Search/filter functionality
- [ ] Achievement badges
- [ ] Export capabilities

---

## 📝 Technical Requirements

### **Database Changes**

**New Table:**
```sql
CREATE TABLE accounts_teamprofile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES auth_user(id),
    priority INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    is_manually_assigned BOOLEAN DEFAULT FALSE,
    last_promoted TIMESTAMP NULL,
    promotion_notes TEXT
);

CREATE INDEX idx_team_priority ON accounts_teamprofile(priority);
CREATE INDEX idx_team_points ON accounts_teamprofile(total_points);
CREATE INDEX idx_team_manual ON accounts_teamprofile(is_manually_assigned);
```

**Groups (using existing table):**
```sql
-- Uses django.contrib.auth.models.Group (already exists)
-- Just INSERT new group records
INSERT INTO auth_group (name) VALUES 
    ('BOG/Leadership'),
    ('Elite Team'),
    ('Lead Team'),
    ('Support Team'),
    ('Senior Analysts'),
    ('Junior Analysts'),
    ('Senior Trainee'),
    ('Junior Trainee'),
    ('Elementary');
```

**No changes to UserProfile table!** ✅

---

## 🔗 Dependencies

**Required:**
- Django 4.x
- PostgreSQL
- Django Groups (built-in)
- Existing UserProfile model

**Optional:**
- Redis (for caching)
- Celery (for background jobs)

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Team Display Accuracy | 100% | All 14 members in correct categories |
| Page Load Time | < 2s | Chrome DevTools |
| Query Count | < 10 | Django Debug Toolbar |
| Admin Satisfaction | High | Stakeholder review |
| Code Coverage | 80%+ | pytest --cov |

---

**Continue to [03_ARCHITECTURE.md](03_ARCHITECTURE.md)**

