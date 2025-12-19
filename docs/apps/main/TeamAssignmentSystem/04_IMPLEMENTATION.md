# Team Assignment System - Implementation

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 🔨 Implementation Guide

---

## 🚀 QUICK START (60-90 Minutes)

### **Prerequisites**
- Django 4.x
- PostgreSQL database
- Python 3.8+
- All team members have User accounts

---

## 📝 IMPLEMENTATION STEPS

### **PHASE 1: Database Setup (Day 1)**

#### **Step 1.1: Create TeamProfile Model**

**File:** `coda/accounts/models.py`

Add this model at the end of the file:

```python
class TeamProfile(models.Model):
    """
    Team-specific metadata. Category stored in Django Groups.
    
    Design: Keep SMALL (5 fields only). Category in Groups, not here.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='team_profile',
        help_text='User this team profile belongs to'
    )
    
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Display priority (higher = shown first within category)'
    )
    
    total_points = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Cached total points (recalculated daily)'
    )
    
    is_manually_assigned = models.BooleanField(
        default=False,
        db_index=True,
        help_text='True = manual assignment, False = points-based'
    )
    
    last_promoted = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When last promoted to manual category'
    )
    
    promotion_notes = models.TextField(
        blank=True,
        help_text='Promotion notes (who, why, when)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_teamprofile'
        verbose_name = 'Team Profile'
        verbose_name_plural = 'Team Profiles'
        indexes = [
            models.Index(fields=['priority', '-total_points']),
            models.Index(fields=['is_manually_assigned']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.category or 'Uncategorized'}"
    
    @property
    def category(self):
        """Get team category from user's groups"""
        TEAM_GROUPS = [
            'BOG/Leadership', 'Elite Team', 'Lead Team', 
            'Support Team', 'Senior Analysts', 'Junior Analysts',
            'Senior Trainee', 'Junior Trainee', 'Elementary',
        ]
        
        for group_name in TEAM_GROUPS:
            if self.user.groups.filter(name=group_name).exists():
                return group_name
        
        return None
```

---

#### **Step 1.2: Create Migration**

```bash
cd coda
python manage.py makemigrations accounts --name create_team_profile
```

**Review migration:**
```bash
python manage.py sqlmigrate accounts XXXX
```

**Expected output:**
```sql
CREATE TABLE "accounts_teamprofile" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL UNIQUE,
    "priority" integer NOT NULL,
    "total_points" integer NOT NULL,
    "is_manually_assigned" boolean NOT NULL,
    "last_promoted" timestamp with time zone NULL,
    "promotion_notes" text NOT NULL,
    "created_at" timestamp with time zone NOT NULL,
    "updated_at" timestamp with time zone NOT NULL
);
```

---

#### **Step 1.3: Run Migration**

```bash
# Dev environment
python manage.py migrate

# Verify
python manage.py dbshell
\d accounts_teamprofile
\q
```

---

### **PHASE 2: Create Team Groups (Day 1)**

#### **Step 2.1: Create Group Setup Command**

**File:** `coda/main/management/commands/create_team_groups.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create Django Groups for team categories'
    
    TEAM_GROUPS = [
        'BOG/Leadership',
        'Elite Team',
        'Lead Team',
        'Support Team',
        'Senior Analysts',
        'Junior Analysts',
        'Senior Trainee',
        'Junior Trainee',
        'Elementary',
    ]
    
    def handle(self, *args, **options):
        self.stdout.write('Creating team groups...\n')
        
        for group_name in self.TEAM_GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Created: {group_name}')
                )
            else:
                self.stdout.write(
                    f'  ⏭️  Exists: {group_name}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Created/verified {len(self.TEAM_GROUPS)} groups')
        )
```

---

#### **Step 2.2: Run Group Creation**

```bash
python manage.py create_team_groups
```

**Verify:**
```bash
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.filter(name__icontains='Team').count()
# Should show team groups
```

---

### **PHASE 3: Assign Manual Categories (Day 2)**

**Use the management command created earlier:**

```bash
# Dry run first
python manage.py assign_manual_team_members --dry-run

# Actually assign
python manage.py assign_manual_team_members
```

**What happens:**
1. Creates/updates TeamProfile for each member
2. Adds user to Django Group
3. Sets priority
4. Marks as manually_assigned

---

### **PHASE 4: Calculate Points (Day 2)**

```bash
# Calculate points for trainees
python manage.py recalculate_team_points --verbose

# Check promotion candidates
python manage.py show_promotion_candidates --detailed
```

---

### **PHASE 5: Update Views (Day 3)**

#### **Step 5.1: Create TeamService**

**File:** `coda/main/services/team_service.py`

(See 03_ARCHITECTURE.md for complete implementation)

---

#### **Step 5.2: Update team() View**

**File:** `coda/main/views.py`

**Replace existing team() function (lines 739-928) with:**

```python
def team(request, title):
    """
    Main team view using Groups + TeamProfile.
    
    Simplified from 190 lines to ~60 lines!
    """
    from django.contrib.auth.models import Group
    
    # Define categories for each page
    if title == 'team_profiles':
        categories = [
            'BOG/Leadership',
            'Elite Team',
            'Lead Team',
            'Support Team',
            'Senior Analysts',
            'Junior Analysts',
        ]
        heading = "THE BEST TEAM IN ANALYTICS AND WEB DEVELOPMENT"
        
    elif title == 'future_talents':
        categories = [
            'Senior Trainee',
            'Junior Trainee',
            'Elementary',
        ]
        heading = "MINDS OF TOMORROW: LEADING DATA ANALYTICS AND WEB DEVELOPMENT"
        
    elif title == 'board':
        categories = ['BOG/Leadership']
        heading = "BOARD OF GOVERNORS"
        
    else:
        categories = []
        heading = "TEAM"
    
    # Get team members for each category
    team_categories = {}
    
    for category_name in categories:
        # Query by group (simple!)
        members = User.objects.filter(
            groups__name=category_name,
            is_active=True
        ).select_related(
            'profile',
            'team_profile'
        ).order_by(
            'team_profile__priority',
            '-team_profile__total_points',
            'date_joined'
        )
        
        if members.exists():
            team_categories[category_name] = members
    
    # Get promotion candidates (admin only)
    promotion_candidates = []
    if request.user.is_staff:
        from accounts.models import TeamProfile
        promotion_candidates = User.objects.filter(
            team_profile__is_manually_assigned=False,
            team_profile__total_points__gte=6000,
            is_active=True
        ).select_related('team_profile')
    
    context = {
        'team_categories': team_categories,
        'promotion_candidates': promotion_candidates,
        'title': heading,
    }
    
    return render(request, 'main/team_profiles.html', context)
```

**Lines of code:** ~60 (vs 190 before)  
**Complexity:** Low  
**Queries:** 1-2 per category (vs 5+ per member before)

---

### **PHASE 6: Testing (Day 4)**

```bash
# Run tests
pytest tests/test_team_*.py -v

# Check coverage
pytest --cov=main.services.team_service --cov-report=html
```

---

### **PHASE 7: Deployment (Day 5)**

See [07_DEPLOYMENT.md](07_DEPLOYMENT.md) for detailed deployment steps.

---

## 📋 Complete File Checklist

### **Models**
- [x] `coda/accounts/models.py` - Add TeamProfile model

### **Services**
- [x] `coda/main/services/team_service.py` - Create service

### **Views**
- [x] `coda/main/views.py` - Update team() view

### **Management Commands**
- [x] `create_team_groups.py`
- [x] `verify_team_members.py`
- [x] `assign_manual_team_members.py`
- [x] `recalculate_team_points.py`
- [x] `show_promotion_candidates.py`
- [x] `promote_team_member.py`

### **Tests**
- [ ] `tests/test_team_profile_model.py`
- [ ] `tests/test_team_service.py`
- [ ] `tests/test_team_views.py`

### **Documentation**
- [x] All 7 docs in TeamAssignmentSystem/

---

## 🎯 Implementation Priority

### **Critical Path (Must Do)**
1. ✅ Create TeamProfile model
2. ✅ Run migration
3. ✅ Create team groups
4. ✅ Assign manual members
5. ✅ Update team() view

### **Important (Should Do)**
6. ✅ Calculate points
7. ✅ Write tests
8. ✅ Deploy to UAT

### **Nice to Have (Can Wait)**
9. ⏰ Add page caching
10. ⏰ Create individual member pages
11. ⏰ Add search/filter

---

**Continue to [05_TESTING.md](05_TESTING.md)**

