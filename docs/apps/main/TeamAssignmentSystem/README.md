# Team Assignment System

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Status:** 🚀 Ready for Implementation  
**Last Updated:** November 5, 2025

---

## 📋 OVERVIEW

Team Assignment System enables both **manual assignment** of established team members and **automated points-based categorization** of future talents, using Django's built-in Groups plus a lightweight TeamProfile model.

**Current State:**
- ❌ Hardcoded team logic in views
- ❌ 100+ queries per page load
- ❌ No BOG/Leadership category
- ❌ No manual assignment capability

**Target State:**
- ✅ Django Groups for team categories
- ✅ TeamProfile model for metadata (5 fields only!)
- ✅ Manual assignment for senior roles
- ✅ Points-based auto-assignment for trainees
- ✅ Zero UserProfile bloat (stays at 38 fields)
- ✅ < 10 queries per page load

---

## 📚 DOCUMENTATION

| Document | Purpose | Read If... |
|----------|---------|-----------|
| **[01_ANALYSIS.md](01_ANALYSIS.md)** | Business case, current state, defects | New to project or planning |
| **[02_REQUIREMENTS.md](02_REQUIREMENTS.md)** | Detailed requirements, team structure | Defining scope |
| **[03_ARCHITECTURE.md](03_ARCHITECTURE.md)** | System design, data models, flows | Implementing or reviewing design |
| **[04_IMPLEMENTATION.md](04_IMPLEMENTATION.md)** | Step-by-step code implementation | Building the system |
| **[05_TESTING.md](05_TESTING.md)** | Test strategy, test cases | Writing tests |
| **[06_MAINTENANCE.md](06_MAINTENANCE.md)** | Operations, monitoring, troubleshooting | Running in production |
| **[07_DEPLOYMENT.md](07_DEPLOYMENT.md)** | Deployment steps, rollback | Deploying to UAT/Production |

---

## 🎯 KEY FEATURES

### **✅ Implemented** (After this feature)
- Manual team assignment (BOG, Elite, Lead, Support, Senior/Junior Analysts)
- Points-based auto-assignment (Senior/Junior Trainees, Elementary)
- Django Groups integration
- TeamProfile model (5 fields)
- Promotion candidate detection
- Management commands (6 commands)
- Cached point calculation
- Admin interface

### **📋 Planned** (Future Enhancements)
- Individual member detail pages
- Search/filter functionality
- Achievement badges
- Team member projects showcase
- Performance dashboards

---

## 🔑 KEY URLS

- `/about/` - About page with team preview
- `/members/team_profiles` - Established team (manual assignments)
- `/members/future_talents` - Future talents (points-based)
- `/members/board` - Board of Governors

---

## 🏗️ ARCHITECTURE HIGHLIGHTS

### **Team Categories**

**Manual (6 categories):**
- BOG/Leadership (3 members)
- Elite Team (1 member)
- Lead Team (3 members)
- Support Team (2 members)
- Senior Analysts (1 member)
- Junior Analysts (1 member)

**Points-Based (3 categories):**
- Senior Trainee (5,000-6,000 points)
- Junior Trainee (4,000-5,000 points)
- Elementary (<4,000 points)

### **Data Models**

```python
# Django's built-in Group (no changes needed)
- name: 'BOG/Leadership', 'Elite Team', etc.

# New TeamProfile model (5 fields only!)
- user (FK to User)
- priority (for ordering)
- total_points (cached)
- is_manually_assigned (manual vs auto)
- last_promoted (timestamp)
- promotion_notes (text)

# UserProfile (NO CHANGES!)
- Stays at 38 fields ✅
```

---

## 🚀 QUICK START

```bash
# Step 1: Create migration
python manage.py makemigrations accounts --name create_team_profile

# Step 2: Run migration
python manage.py migrate

# Step 3: Create team groups
python manage.py create_team_groups

# Step 4: Assign manual categories
python manage.py assign_manual_team_members

# Step 5: Calculate points
python manage.py recalculate_team_points

# Step 6: Test
python manage.py runserver
# Visit: http://localhost:8000/members/team_profiles
```

**Full guide:** See [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md)

---

## ⏱️ IMPLEMENTATION TIMELINE

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 1** | Day 1 | Create TeamProfile model, run migration |
| **Phase 2** | Day 2 | Create groups, assign manual members |
| **Phase 3** | Day 3 | Calculate points, update views |
| **Phase 4** | Day 4 | Testing and refinement |
| **Phase 5** | Day 5 | Deploy to UAT |

**Total:** 5 days (1 week)

---

## 🎯 SUCCESS CRITERIA

After implementation:

- [ ] BOG/Leadership: 3 members (Amanda, Chris M., Tirimba)
- [ ] Elite Team: 1 member (Chris M. - coda-info)
- [ ] Lead Team: 3 members (Edwin, Emanuel, George)
- [ ] Support Team: 2 members (Hashim, Christine)
- [ ] Senior Analysts: 1 member (Sylvia)
- [ ] Junior Analysts: 1 member (Phinehas)
- [ ] Future talents auto-categorized by points
- [ ] Page loads < 2 seconds
- [ ] UserProfile stays at 38 fields ✅
- [ ] No hardcoded usernames

---

## 📞 QUICK REFERENCE

### **Management Commands**
```bash
verify_team_members              # Check all members exist
create_team_groups              # Create Django Groups
assign_manual_team_members      # Assign manual categories
recalculate_team_points         # Calculate points
show_promotion_candidates       # Show who's ready
promote_team_member <user> <cat> # Promote someone
```

### **Key Files**
- Models: `coda/accounts/models.py` (TeamProfile)
- Views: `coda/main/views.py` (team, about)
- Templates: `coda/main/templates/main/team_profiles.html`
- Commands: `coda/main/management/commands/`

---

## 🔗 RELATED SYSTEMS

- **Accounts App** - User and profile management
- **Management App** - Task history (provides points)
- **Professional Services** - Client assessments (provides points)
- **Finance** - Performance tier (uses team data)

---

## 📊 PERFORMANCE

**Before:**
- 100-120 queries per page
- 3-43 second load times
- No caching

**After:**
- 5-10 queries per page (95% reduction)
- < 2 second load times
- Points cached daily

---

## 💡 WHY THIS APPROACH?

**Groups + TeamProfile vs Fields:**

| Approach | UserProfile Size | Architecture | Recommendation |
|----------|-----------------|--------------|----------------|
| 7 Fields in UserProfile | 45 fields ⚠️ | Simple | Quick ship |
| **Groups + TeamProfile** | **38 fields ✅** | **Clean** | **Best** ⭐ |

**Decision:** Use Groups + TeamProfile
- Solves "too many fields" concern
- Clean separation of concerns
- Uses Django's built-in Groups
- Best practices architecture

---

**📖 Start with [01_ANALYSIS.md](01_ANALYSIS.md) to understand the system**

