# Team Assignment System - Maintenance

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 🔧 Maintenance Guide

---

## 🔧 Routine Maintenance

### **Daily Tasks (Automated)**

#### **Point Recalculation**
```bash
# Cron job: Daily at 2 AM
0 2 * * * cd /app/coda && python manage.py recalculate_team_points
```

**What it does:**
- Calculates points for non-manual members
- Updates TeamProfile.total_points
- Auto-categorizes trainees
- Flags promotion candidates

**Monitoring:**
```bash
# Check last run
heroku logs --tail --app codamakutano | grep "recalculate_team_points"

# Verify points are current
python manage.py shell
>>> from accounts.models import TeamProfile
>>> TeamProfile.objects.filter(
...     total_points_calculated_at__lt=timezone.now() - timedelta(days=2)
... ).count()
# Should be 0
```

---

### **Weekly Tasks (Manual)**

#### **Review Promotion Candidates**
```bash
# Every Monday
python manage.py show_promotion_candidates --detailed
```

**Process:**
1. Review each candidate's points
2. Check their recent work/projects
3. Get manager recommendation
4. Promote if ready:
   ```bash
   python manage.py promote_team_member <username> junior_analyst
   ```

---

#### **Verify Team Assignments**
```bash
# Monthly check
python manage.py verify_team_members
```

**Check:**
- All required members exist
- All have profiles
- All in correct categories

---

### **Monthly Tasks**

#### **Audit Team Structure**
```bash
# Run audit report
python manage.py shell

>>> from django.contrib.auth.models import Group, User
>>> from accounts.models import TeamProfile

# Check each category
>>> for group in Group.objects.filter(name__in=TEAM_GROUPS):
...     count = User.objects.filter(groups=group, is_active=True).count()
...     print(f"{group.name}: {count} members")
```

**Expected counts:**
- BOG/Leadership: 3
- Elite Team: 1
- Lead Team: 3
- Support Team: 2
- Senior Analysts: 1
- Junior Analysts: 1
- Senior Trainee: 2+
- Junior Trainee: 2+
- Elementary: varies

---

## 🐛 Troubleshooting

### **Issue 1: Member Not Showing on Page**

**Symptoms:**
- Team member exists but not displayed

**Diagnosis:**
```bash
python manage.py shell

>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='<username>')

# Check 1: User is active?
>>> print(user.is_active)  # Should be True

# Check 2: In a team group?
>>> print(user.groups.filter(name__icontains='Team').values_list('name', flat=True))

# Check 3: Has TeamProfile?
>>> print(hasattr(user, 'team_profile'))  # Should be True

# Check 4: Has UserProfile?
>>> print(hasattr(user, 'profile'))  # Should be True

# Check 5: Has description?
>>> print(user.profile.description)  # Should not be empty
```

**Solutions:**
```bash
# Missing group
>>> from django.contrib.auth.models import Group
>>> group = Group.objects.get(name='Lead Team')
>>> user.groups.add(group)

# Missing TeamProfile
>>> from accounts.models import TeamProfile
>>> TeamProfile.objects.create(user=user)

# Missing description
>>> user.profile.description = "Professional bio here"
>>> user.profile.save()
```

---

### **Issue 2: Wrong Category Displayed**

**Symptoms:**
- Member shows in wrong category

**Diagnosis:**
```bash
>>> user = User.objects.get(username='<username>')
>>> print(user.team_profile.category)  # Shows current category
>>> print(user.groups.all().values_list('name', flat=True))  # All groups
```

**Solution:**
```bash
# Remove from wrong group
>>> wrong_group = Group.objects.get(name='Wrong Team')
>>> user.groups.remove(wrong_group)

# Add to correct group
>>> correct_group = Group.objects.get(name='Correct Team')
>>> user.groups.add(correct_group)
```

---

### **Issue 3: Points Not Updating**

**Symptoms:**
- Points haven't changed in days

**Diagnosis:**
```bash
>>> user = User.objects.get(username='<username>')
>>> print(user.team_profile.total_points)
>>> print(user.team_profile.total_points_calculated_at)
```

**Solution:**
```bash
# Recalculate manually
python manage.py recalculate_team_points

# Or for specific user
python manage.py shell
>>> from main.services.team_service import TeamService
>>> user = User.objects.get(username='<username>')
>>> points = TeamService.calculate_total_points(user)
>>> user.team_profile.total_points = points
>>> user.team_profile.save()
```

---

### **Issue 4: Promotion Candidate Not Flagged**

**Symptoms:**
- User has 6,000+ points but not in promotion list

**Diagnosis:**
```bash
>>> user = User.objects.get(username='<username>')
>>> print(user.team_profile.total_points)  # Check points
>>> print(user.team_profile.is_manually_assigned)  # Should be False
```

**Solution:**
```bash
# If manually assigned, they won't show in candidates
# That's correct - they're already promoted

# If points are wrong, recalculate
python manage.py recalculate_team_points
```

---

### **Issue 5: Image Not Loading**

**Symptoms:**
- Profile image shows fallback

**Diagnosis:**
```bash
>>> user = User.objects.get(username='<username>')
>>> print(user.profile.img_url)  # Check URL
>>> print(user.profile.image)  # Check local file
```

**Solution:**
```bash
# Update image in Django Admin
# Or upload via UserProfile update view
# /updateprofile/<user_id>/
```

---

## 📊 Monitoring

### **Key Metrics to Track**

| Metric | How to Check | Alert If |
|--------|-------------|----------|
| Page Load Time | Chrome DevTools | > 2 seconds |
| Query Count | Django Debug Toolbar | > 10 queries |
| Team Member Count | `show_team_stats` command | Unexpected changes |
| Promotion Candidates | `show_promotion_candidates` | > 5 waiting |
| Points Calculation | Check logs | Failed runs |

---

### **Health Check Script**

```python
# management/commands/team_health_check.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        from django.contrib.auth.models import Group, User
        from accounts.models import TeamProfile
        
        issues = []
        
        # Check 1: All groups exist
        expected_groups = 9
        actual_groups = Group.objects.filter(
            name__in=TEAM_GROUPS
        ).count()
        
        if actual_groups != expected_groups:
            issues.append(f"Missing groups: {expected_groups - actual_groups}")
        
        # Check 2: All active employees have TeamProfile
        employees = User.objects.filter(category=2, is_active=True)
        for user in employees:
            if not hasattr(user, 'team_profile'):
                issues.append(f"Missing TeamProfile: {user.username}")
        
        # Check 3: Points calculation recent
        stale = TeamProfile.objects.filter(
            total_points_calculated_at__lt=timezone.now() - timedelta(days=2)
        ).count()
        
        if stale > 0:
            issues.append(f"Stale points: {stale} profiles")
        
        # Report
        if issues:
            self.stdout.write(self.style.WARNING('\n⚠️ Issues found:'))
            for issue in issues:
                self.stdout.write(f'  • {issue}')
        else:
            self.stdout.write(self.style.SUCCESS('✅ All checks passed'))
```

Run weekly:
```bash
python manage.py team_health_check
```

---

## 🔄 Update Procedures

### **Adding a New Team Member**

```bash
# 1. Verify user exists
python manage.py shell
>>> User.objects.filter(username='<new_username>').exists()

# 2. Assign to category
python manage.py promote_team_member <username> <category>

# Or via shell
>>> from main.services.team_service import TeamService
>>> user = User.objects.get(username='<username>')
>>> TeamService.assign_to_category(user, 'Junior Analyst', priority=50)

# 3. Verify on page
# Visit /members/team_profiles
```

---

### **Changing Team Categories**

```bash
# Move someone from Junior to Senior Analyst
python manage.py promote_team_member <username> senior_analyst --priority 80

# Via shell
>>> user = User.objects.get(username='<username>')
>>> user.groups.remove(Group.objects.get(name='Junior Analysts'))
>>> user.groups.add(Group.objects.get(name='Senior Analysts'))
>>> user.team_profile.priority = 80
>>> user.team_profile.save()
```

---

### **Updating Team Priorities**

```bash
# Change display order within category
python manage.py shell

>>> user = User.objects.get(username='<username>')
>>> user.team_profile.priority = 95
>>> user.team_profile.save()

# Bulk update
>>> from accounts.models import TeamProfile
>>> TeamProfile.objects.filter(
...     user__groups__name='Lead Team'
... ).update(priority=90)
```

---

## 🚨 Common Issues & Solutions

### **Issue: Duplicate Group Membership**

**Problem:** User in multiple team groups

**Fix:**
```python
# Clean up - user should only be in ONE team group
from django.contrib.auth.models import Group

TEAM_GROUPS = ['BOG/Leadership', 'Elite Team', ...]

for user in User.objects.filter(is_active=True):
    team_groups = user.groups.filter(name__in=TEAM_GROUPS)
    
    if team_groups.count() > 1:
        print(f"⚠️ {user.username} in {team_groups.count()} groups")
        # Keep first, remove others
        keep = team_groups.first()
        for group in team_groups.exclude(id=keep.id):
            user.groups.remove(group)
```

---

### **Issue: TeamProfile Missing**

**Problem:** User has no TeamProfile

**Fix:**
```python
# Auto-create for all employees
from accounts.models import TeamProfile

for user in User.objects.filter(category=2, is_active=True):
    TeamProfile.objects.get_or_create(user=user)
```

---

### **Issue: Points Calculation Failed**

**Problem:** Point calculation throws error

**Fix:**
```python
# Check logs
heroku logs --tail --app codamakutano | grep ERROR

# Manually recalculate with error handling
from main.services.team_service import TeamService

for user in User.objects.filter(team_profile__is_manually_assigned=False):
    try:
        points = TeamService.calculate_total_points(user)
        user.team_profile.total_points = points
        user.team_profile.save()
        print(f"✅ {user.username}: {points}")
    except Exception as e:
        print(f"❌ {user.username}: {e}")
```

---

## 📈 Performance Monitoring

### **Query Performance**

```sql
-- Slow query detection
SELECT * FROM pg_stat_statements 
WHERE query LIKE '%accounts_teamprofile%' 
AND mean_time > 100 
ORDER BY mean_time DESC;
```

---

### **Cache Hit Rate**

```bash
# If using Redis
redis-cli INFO stats | grep keyspace_hits
redis-cli INFO stats | grep keyspace_misses

# Calculate hit rate
# Hit rate = hits / (hits + misses)
# Target: > 90%
```

---

## 🔄 Backup & Recovery

### **Backup TeamProfile Data**

```bash
# Backup before major changes
python manage.py dumpdata accounts.TeamProfile > backup_teamprofile.json

# Restore if needed
python manage.py loaddata backup_teamprofile.json
```

---

### **Backup Group Assignments**

```bash
# Export group memberships
python manage.py shell

>>> import json
>>> from django.contrib.auth.models import User
>>> 
>>> data = []
>>> for user in User.objects.filter(is_active=True):
...     groups = list(user.groups.values_list('name', flat=True))
...     data.append({'username': user.username, 'groups': groups})
>>> 
>>> with open('group_backup.json', 'w') as f:
...     json.dump(data, f, indent=2)
```

---

## 📝 Change Log Template

### **Team Assignment Changes**

```markdown
# Team Assignment Change Log

## YYYY-MM-DD - Promotion
- **Member:** John Doe
- **From:** Senior Trainee (5,200 points)
- **To:** Junior Analyst
- **Reason:** Completed 3 major projects, positive reviews
- **Approved by:** Admin Name

## YYYY-MM-DD - Priority Update
- **Category:** Lead Team
- **Change:** Reordered priorities
- **Reason:** Reflect current responsibilities
```

---

## 🎯 Known Issues

### **Issue: Cached Page Shows Old Data**

**Severity:** Low  
**Impact:** Team changes not visible for up to 1 hour  
**Workaround:** Clear cache manually  
**Fix:** Invalidate cache on team changes

```python
# In assignment code
from django.core.cache import cache
cache.delete('team_profiles_page')
```

---

### **Issue: Group Permissions Side Effects**

**Severity:** Low  
**Impact:** Team groups might be used for permissions  
**Workaround:** Use separate groups for permissions  
**Fix:** Namespace team groups (e.g., "TEAM: Lead")

---

## 📊 System Health Indicators

### **Green (Healthy)**
- ✅ All team members have TeamProfile
- ✅ Points calculated within 24 hours
- ✅ Page loads < 2 seconds
- ✅ No duplicate group memberships
- ✅ All required members assigned

### **Yellow (Warning)**
- ⚠️ Points > 48 hours old
- ⚠️ Page loads 2-3 seconds
- ⚠️ Promotion candidates waiting > 7 days
- ⚠️ Missing profile images

### **Red (Critical)**
- ❌ TeamProfile missing for active users
- ❌ Page loads > 3 seconds
- ❌ Point calculation failing
- ❌ Required members not assigned

---

## 🔧 Maintenance Commands

```bash
# Health check
python manage.py team_health_check

# Recalculate points
python manage.py recalculate_team_points

# Show promotion candidates
python manage.py show_promotion_candidates

# Verify all members
python manage.py verify_team_members

# Reassign if needed
python manage.py assign_manual_team_members --force

# Promote member
python manage.py promote_team_member <username> <category>
```

---

## 📝 Incident Response

### **Team Page Not Loading**

```bash
# 1. Check server status
heroku ps --app codamakutano

# 2. Check recent changes
git log --oneline -10

# 3. Check error logs
heroku logs --tail --app codamakutano

# 4. Rollback if needed
git revert HEAD
git push heroku main
```

---

### **Wrong Member Displayed**

```bash
# 1. Check group assignment
python manage.py shell
>>> user = User.objects.get(username='<username>')
>>> print(user.groups.all())

# 2. Fix assignment
>>> from main.services.team_service import TeamService
>>> TeamService.assign_to_category(user, 'Correct Team', priority=100)

# 3. Clear cache
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 📈 Performance Optimization

### **If Page Loads Slow**

```bash
# 1. Check query count
# Install django-debug-toolbar

# 2. Check indexes
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT * FROM pg_indexes WHERE tablename = 'accounts_teamprofile';")
>>> for row in cursor.fetchall():
...     print(row)

# 3. Add missing indexes if needed
# Update models.py and run makemigrations
```

---

## 🔄 Regular Maintenance Schedule

| Task | Frequency | Duration | Owner |
|------|-----------|----------|-------|
| Point recalculation | Daily (auto) | 2 min | System |
| Review promotions | Weekly | 15 min | Admin |
| Verify assignments | Monthly | 10 min | Admin |
| Audit team structure | Monthly | 20 min | Admin |
| Performance review | Quarterly | 1 hour | Dev Team |
| Backup team data | Weekly | 5 min | System |

---

**Continue to [07_DEPLOYMENT.md](07_DEPLOYMENT.md)**

