# QUICK START GUIDE - Hybrid Team System

**Created:** November 5, 2025  
**Purpose:** Step-by-step guide to implement hybrid team assignment system

---

## 🚀 IMPLEMENTATION STEPS

### **Step 1: Verify Team Members Exist (5 minutes)**

```bash
cd coda
python manage.py verify_team_members
```

**What this does:**
- Checks if all 14 required team members have user accounts
- Checks if they have UserProfile records
- Shows what's missing

**If users are missing:**
```bash
python manage.py verify_team_members --create-missing
```

---

### **Step 2: Create Migration (2 minutes)**

```bash
python manage.py makemigrations accounts --name add_hybrid_team_fields
```

**Review the migration:**
```bash
python manage.py sqlmigrate accounts XXXX
```

**Run the migration:**
```bash
# Dev environment
python manage.py migrate

# UAT (after testing in dev)
heroku run "cd coda && python manage.py migrate" --app codamakutano
```

**What this adds:**
- `is_manually_assigned` - Boolean flag
- `team_category_manual` - Manual category assignment
- `team_priority` - Display priority
- `total_points` - Cached points
- `total_points_calculated_at` - When calculated
- `last_promoted` - Promotion timestamp
- `promotion_notes` - Promotion notes

---

### **Step 3: Assign Manual Categories (5 minutes)**

```bash
# Dry run first (see what would happen)
python manage.py assign_manual_team_members --dry-run

# Actually assign
python manage.py assign_manual_team_members
```

**What this does:**
- Assigns 10 team members to manual categories:
  - 3 to BOG/Leadership
  - 1 to Elite
  - 3 to Lead Team
  - 2 to Support Team
  - 1 to Senior Analyst
  - 1 to Junior Analyst

**Verify assignments:**
```bash
python manage.py shell
>>> from accounts.models import UserProfile
>>> manual = UserProfile.objects.filter(is_manually_assigned=True)
>>> print(f"Manual assignments: {manual.count()}")  # Should be 10
>>> for p in manual:
...     print(f"{p.user.username}: {p.team_category_manual}")
```

---

### **Step 4: Calculate Points for Future Talents (5 minutes)**

```bash
# Dry run first
python manage.py recalculate_team_points --dry-run --verbose

# Actually calculate
python manage.py recalculate_team_points --verbose
```

**What this does:**
- Calculates points for 4 future talent members:
  - Bonie Luke
  - Brenda Nasimiyu
  - Angel
  - Eugene
- Caches points in database
- Shows point breakdown
- Identifies promotion candidates (6,000+ points)

**Check results:**
```bash
python manage.py shell
>>> from accounts.models import UserProfile
>>> future_talents = UserProfile.objects.filter(is_manually_assigned=False)
>>> for p in future_talents:
...     category = 'senior_trainee' if p.total_points >= 5000 else 'junior_trainee' if p.total_points >= 4000 else 'elementary'
...     print(f"{p.user.username}: {p.total_points} points → {category}")
```

---

### **Step 5: Check Promotion Candidates (2 minutes)**

```bash
python manage.py show_promotion_candidates --detailed
```

**What this does:**
- Shows trainees with 6,000+ points
- These are ready for manual promotion to Junior Analyst
- Admin reviews and promotes manually

---

### **Step 6: Update UserProfile Model (10 minutes)**

Add the helper method to `coda/accounts/models.py`:

```python
class UserProfile(models.Model):
    # ... existing fields ...
    
    # New fields (added by migration)
    is_manually_assigned = models.BooleanField(default=False)
    team_category_manual = models.CharField(max_length=50, null=True, blank=True)
    team_priority = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0, db_index=True)
    total_points_calculated_at = models.DateTimeField(null=True, blank=True)
    last_promoted = models.DateTimeField(null=True, blank=True)
    promotion_notes = models.TextField(blank=True)
    
    def get_team_category(self):
        """
        Get team category (manual takes precedence over points).
        
        Returns:
            str: Category slug (bog_leadership, elite, lead, etc.)
        """
        if self.is_manually_assigned and self.team_category_manual:
            return self.team_category_manual
        else:
            return self._category_from_points()
    
    def _category_from_points(self):
        """Calculate category from points (for future talents)"""
        if self.total_points >= 6000:
            return 'ready_for_promotion'
        elif self.total_points >= 5000:
            return 'senior_trainee'
        elif self.total_points >= 4000:
            return 'junior_trainee'
        else:
            return 'elementary'
    
    def get_team_category_display(self):
        """Get human-readable category name"""
        category_names = {
            'bog_leadership': 'BOG/Leadership',
            'elite': 'Elite Team',
            'lead': 'Lead Team',
            'support': 'Support Team',
            'senior_analyst': 'Senior Analysts',
            'junior_analyst': 'Junior Analysts',
            'senior_trainee': 'Senior Trainee',
            'junior_trainee': 'Junior Trainee',
            'elementary': 'Elementary',
            'ready_for_promotion': 'Ready for Promotion',
        }
        return category_names.get(self.get_team_category(), 'Unknown')
```

---

### **Step 7: Update Team View (15 minutes)**

Update `coda/main/views.py`:

```python
def team(request, title):
    """Main team view with hybrid assignment"""
    
    # Define categories for each page
    if title == 'team_profiles':
        categories = [
            ('bog_leadership', 'BOG/Leadership'),
            ('elite', 'Elite Team'),
            ('lead', 'Lead Team'),
            ('support', 'Support Team'),
            ('senior_analyst', 'Senior Analysts'),
            ('junior_analyst', 'Junior Analysts'),
        ]
        heading = "THE BEST TEAM IN ANALYTICS AND WEB DEVELOPMENT"
        
    elif title == 'future_talents':
        categories = [
            ('senior_trainee', 'Senior Trainee Team'),
            ('junior_trainee', 'Junior Trainee Team'),
            ('elementary', 'Elementary'),
        ]
        heading = "MINDS OF TOMORROW"
        
    elif title == 'board':
        categories = [('bog_leadership', 'Board of Governors')]
        heading = "THE BOG"
    else:
        categories = []
        heading = "TEAM"
    
    # Get team members for each category
    team_categories = {}
    
    for category_slug, category_name in categories:
        # Check if manual category
        is_manual = category_slug in ['bog_leadership', 'elite', 'lead', 'support', 'senior_analyst', 'junior_analyst']
        
        if is_manual:
            # Manual assignment - filter by flag
            members = UserProfile.objects.filter(
                is_manually_assigned=True,
                team_category_manual=category_slug,
                user__is_active=True,
                user__category=2  # Employee
            ).select_related('user', 'image2').order_by(
                'team_priority',
                'user__date_joined'
            )
        else:
            # Points-based - filter by point range
            if category_slug == 'senior_trainee':
                members = UserProfile.objects.filter(
                    is_manually_assigned=False,
                    total_points__gte=5000,
                    total_points__lt=6000,
                    user__is_active=True,
                    user__category=2
                ).select_related('user', 'image2').order_by('-total_points')
                
            elif category_slug == 'junior_trainee':
                members = UserProfile.objects.filter(
                    is_manually_assigned=False,
                    total_points__gte=4000,
                    total_points__lt=5000,
                    user__is_active=True,
                    user__category=2
                ).select_related('user', 'image2').order_by('-total_points')
                
            elif category_slug == 'elementary':
                members = UserProfile.objects.filter(
                    is_manually_assigned=False,
                    total_points__lt=4000,
                    user__is_active=True,
                    user__category=2
                ).select_related('user', 'image2').order_by('-total_points')
            else:
                members = UserProfile.objects.none()
        
        if members.exists():
            team_categories[category_name] = members
    
    # Get promotion candidates (if admin)
    promotion_candidates = []
    if request.user.is_staff:
        promotion_candidates = UserProfile.objects.filter(
            is_manually_assigned=False,
            total_points__gte=6000,
            user__is_active=True,
            user__category=2
        ).select_related('user').order_by('-total_points')
    
    context = {
        'team_categories': team_categories,
        'promotion_candidates': promotion_candidates,
        'title': heading,
    }
    
    return render(request, 'main/team_profiles.html', context)
```

---

### **Step 8: Test Locally (10 minutes)**

```bash
# Start dev server
python manage.py runserver

# Test URLs
# http://localhost:8000/about/
# http://localhost:8000/members/team_profiles
# http://localhost:8000/members/future_talents
# http://localhost:8000/members/board
```

**Check:**
- [ ] BOG/Leadership shows 3 members
- [ ] Elite Team shows 1 member
- [ ] Lead Team shows 3 members
- [ ] Support Team shows 2 members
- [ ] Senior Analysts shows 1 member
- [ ] Junior Analysts shows 1 member
- [ ] Future talents page shows trainees by points
- [ ] Images load correctly
- [ ] Admin sees promotion candidates

---

### **Step 9: Deploy to UAT (10 minutes)**

```bash
# Backup database first!
heroku pg:backups:capture --app codamakutano

# Push code
git add -A
git commit -m "Add hybrid team assignment system"
git push uat 25.10_CODA_UAT_CM

# Run migration
heroku run "cd coda && python manage.py migrate" --app codamakutano

# Verify team members
heroku run "cd coda && python manage.py verify_team_members" --app codamakutano

# Assign manual categories
heroku run "cd coda && python manage.py assign_manual_team_members" --app codamakutano

# Calculate points
heroku run "cd coda && python manage.py recalculate_team_points" --app codamakutano

# Test
# https://codamakutano.herokuapp.com/members/team_profiles
```

---

### **Step 10: Schedule Daily Point Recalculation (5 minutes)**

Add to Heroku Scheduler (or crontab):

```bash
# Daily at 2 AM
cd coda && python manage.py recalculate_team_points
```

**Or in Heroku:**
```bash
heroku addons:create scheduler:standard --app codamakutano
heroku addons:open scheduler --app codamakutano

# Add job:
# Command: cd coda && python manage.py recalculate_team_points
# Frequency: Daily at 2:00 AM
```

---

## 📋 COMPLETE COMMAND REFERENCE

```bash
# Verification
python manage.py verify_team_members                    # Check all members exist
python manage.py verify_team_members --create-missing   # Create missing users

# Migration
python manage.py makemigrations accounts --name add_hybrid_team_fields
python manage.py migrate

# Assignment
python manage.py assign_manual_team_members             # Assign manual categories
python manage.py assign_manual_team_members --dry-run   # See what would happen
python manage.py assign_manual_team_members --force     # Reassign existing

# Point Calculation
python manage.py recalculate_team_points                # Calculate for future talents
python manage.py recalculate_team_points --all          # Calculate for everyone
python manage.py recalculate_team_points --verbose      # Show detailed breakdown
python manage.py recalculate_team_points --dry-run      # See without saving

# Promotion
python manage.py show_promotion_candidates              # Show who's ready
python manage.py show_promotion_candidates --detailed   # Show with point breakdown
python manage.py promote_team_member <username> <category>  # Promote someone
python manage.py promote_team_member phinehas_maina junior_analyst --priority 100
```

---

## ✅ SUCCESS CRITERIA

After implementation, verify:

- [ ] 3 members in BOG/Leadership (Amanda, Chris M., Tirimba)
- [ ] 1 member in Elite Team (Chris M. - coda-info)
- [ ] 3 members in Lead Team (Edwin, Emanuel, George)
- [ ] 2 members in Support Team (Hashim, Christine)
- [ ] 1 member in Senior Analysts (Sylvia)
- [ ] 1 member in Junior Analysts (Phinehas)
- [ ] Future talents categorized by points
- [ ] Page loads < 2 seconds
- [ ] Images display correctly
- [ ] Admin sees promotion candidates
- [ ] Non-admin doesn't see points

---

## 🐛 TROUBLESHOOTING

### **Issue: User not found**
```bash
# Check username
python manage.py shell
>>> from accounts.models import CustomerUser
>>> CustomerUser.objects.filter(username__icontains='amanda')

# Create user
>>> CustomerUser.objects.create_user(
...     username='amanda_towe',
...     email='amanda.towe@example.com',
...     first_name='Amanda',
...     last_name='Towe',
...     category=2
... )
```

### **Issue: Profile not found**
```bash
# Profile should auto-create via signal
# If not, create manually:
python manage.py shell
>>> from accounts.models import UserProfile, CustomerUser
>>> user = CustomerUser.objects.get(username='amanda_towe')
>>> UserProfile.objects.create(user=user)
```

### **Issue: Wrong category displayed**
```bash
# Check assignment
python manage.py shell
>>> from accounts.models import UserProfile
>>> p = UserProfile.objects.get(user__username='amanda_towe')
>>> print(f"Manual: {p.is_manually_assigned}")
>>> print(f"Category: {p.team_category_manual}")
>>> print(f"Priority: {p.team_priority}")

# Fix if needed
>>> p.is_manually_assigned = True
>>> p.team_category_manual = 'bog_leadership'
>>> p.team_priority = 100
>>> p.save()
```

### **Issue: Points not calculated**
```bash
# Recalculate for specific user
python manage.py shell
>>> from accounts.models import UserProfile
>>> from main.services.team_service import TeamService
>>> p = UserProfile.objects.get(user__username='bonie_luke')
>>> points = TeamService.calculate_total_points(p)
>>> print(f"Points: {points}")
>>> p.total_points = points
>>> p.save()
```

---

## 🎯 ESTIMATED TIME

**Total implementation time: 60-90 minutes**

- Step 1-2: Database setup (10 min)
- Step 3-5: Data assignment (15 min)
- Step 6-7: Code changes (25 min)
- Step 8: Testing (10 min)
- Step 9: Deployment (15 min)
- Step 10: Scheduling (5 min)

---

**Ready to begin? Start with Step 1!**

