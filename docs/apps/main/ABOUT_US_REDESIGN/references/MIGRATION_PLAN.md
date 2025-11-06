# MIGRATION PLAN - Team Structure Updates

**Document:** 5 of 7  
**Created:** November 5, 2025  
**Purpose:** Step-by-step migration plan for updating team structure

---

## 🎯 MIGRATION GOALS

1. ✅ Update team structure to match new requirements
2. ✅ Assign BOG/Leadership members
3. ✅ Assign Elite Team member
4. ✅ Verify all team members have correct assignments
5. ✅ Update data model if needed
6. ✅ Test all changes
7. ✅ Deploy to UAT
8. ✅ Deploy to production

---

## 📋 CURRENT TEAM STRUCTURE

### **Current State:**
- Elite Team: Hardcoded `c_maghas` (superuser)
- Lead Team: Points-based (>8,000)
- Support Team: Points-based contractors (>1,000)
- Senior Analysts: Points-based (7,000-8,000)
- Junior Analysts: Points-based (6,000-7,000)
- Senior Trainee: Points-based (5,000-6,000)
- Junior Trainee: Points-based (4,000-5,000)
- Elementary: Points-based (<4,000)
- BOG: Filtered by sub_category=0

### **Issues:**
- ❌ No BOG/Leadership category
- ❌ Hardcoded username
- ❌ No manual assignments
- ❌ Missing team members

---

## 🎯 NEW TEAM STRUCTURE

### **BOG/Leadership** (Manual Assignment)
- ✅ Amanda Towe
- ✅ Chris Maghas (username: `cmaghas`)
- ✅ Tirimba Obonyo

### **Elite Team** (Manual Assignment)
- ✅ Chris Maghas (username: `coda-info`)

### **Lead Team** (Points-based or Manual)
- ✅ Edwin Kimtai
- ✅ Emanuel Masakhwe
- ✅ George Ndahiro

### **Support Team** (Contractors - Points-based or Manual)
- ✅ Hashim Kha
- ✅ Christine Karagu

### **Senior Analysts** (Points-based)
- ✅ Sylvia Jelante

### **Junior Analysts** (Points-based)
- ✅ Phinehas Maina

### **Senior Trainee** (Points-based)
- ✅ Bonie Luke
- ✅ Brenda Nasimiyu

### **Junior Trainee** (Points-based)
- ✅ Angel
- ✅ Eugene

---

## 📝 MIGRATION STEPS

### **Phase 1: Data Verification (Day 1)**

#### **Step 1.1: Verify User Accounts Exist**
```python
# management/commands/verify_team_members.py

REQUIRED_MEMBERS = {
    'bog_leadership': [
        ('amanda_towe', 'Amanda Towe'),
        ('cmaghas', 'Chris Maghas'),
        ('tirimba_obonyo', 'Tirimba Obonyo'),
    ],
    'elite_team': [
        ('coda-info', 'Chris Maghas'),
    ],
    'lead_team': [
        ('edwin_kimtai', 'Edwin Kimtai'),
        ('emanuel_masakhwe', 'Emanuel Masakhwe'),
        ('george_ndahiro', 'George Ndahiro'),
    ],
    'support_team': [
        ('hashim_kha', 'Hashim Kha'),
        ('christine_karagu', 'Christine Karagu'),
    ],
    'senior_analyst': [
        ('sylvia_jelante', 'Sylvia Jelante'),
    ],
    'junior_analyst': [
        ('phinehas_maina', 'Phinehas Maina'),
    ],
    'senior_trainee': [
        ('bonie_luke', 'Bonie Luke'),
        ('brenda_nasimiyu', 'Brenda Nasimiyu'),
    ],
    'junior_trainee': [
        ('angel', 'Angel'),
        ('eugene', 'Eugene'),
    ],
}

def verify_users():
    missing = []
    for category, members in REQUIRED_MEMBERS.items():
        for username, full_name in members:
            try:
                user = User.objects.get(username=username)
                print(f"✅ {full_name} ({username}) exists")
            except User.DoesNotExist:
                missing.append((username, full_name, category))
                print(f"❌ {full_name} ({username}) MISSING")
    
    return missing
```

**Action Items:**
- [ ] Run verification script
- [ ] Create missing user accounts
- [ ] Verify all usernames are correct
- [ ] Document any discrepancies

---

#### **Step 1.2: Verify UserProfile Records**
```python
def verify_profiles():
    missing_profiles = []
    for username, full_name, category in REQUIRED_MEMBERS:
        user = User.objects.get(username=username)
        try:
            profile = user.profile
            print(f"✅ Profile exists for {full_name}")
        except UserProfile.DoesNotExist:
            missing_profiles.append((username, full_name))
            print(f"❌ Profile missing for {full_name}")
    
    return missing_profiles
```

**Action Items:**
- [ ] Run profile verification
- [ ] Create missing profiles
- [ ] Verify all profiles have images
- [ ] Verify all profiles have descriptions

---

#### **Step 1.3: Verify Current Team Assignments**
```python
def check_current_assignments():
    results = {}
    for username, full_name, category in REQUIRED_MEMBERS:
        user = User.objects.get(username=username)
        profile = user.profile
        
        # Check current points
        points = calculate_current_points(profile)
        
        # Check current category (if any)
        current_category = get_current_category(profile)
        
        results[username] = {
            'name': full_name,
            'expected_category': category,
            'current_category': current_category,
            'points': points,
        }
    
    return results
```

**Action Items:**
- [ ] Run assignment check
- [ ] Document current vs expected
- [ ] Identify conflicts

---

### **Phase 2: Data Model Updates (Day 2)**

#### **Step 2.1: Create Migration for New Fields**

**Option A: Add Fields to UserProfile**
```python
# migrations/XXXX_add_team_assignment_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='team_category',
            field=models.CharField(
                max_length=50,
                null=True,
                blank=True,
                choices=[
                    ('bog_leadership', 'BOG/Leadership'),
                    ('elite', 'Elite Team'),
                    ('lead', 'Lead Team'),
                    ('support', 'Support Team'),
                    ('senior_analyst', 'Senior Analysts'),
                    ('junior_analyst', 'Junior Analysts'),
                    ('senior_trainee', 'Senior Trainee'),
                    ('junior_trainee', 'Junior Trainee'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='team_priority',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_manually_assigned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='total_points',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='total_points_calculated_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
```

**Option B: Create TeamAssignment Model**
```python
# migrations/XXXX_create_team_assignment.py

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamAssignment',
            fields=[
                ('id', models.AutoField(...)),
                ('category', models.CharField(max_length=50, choices=[...])),
                ('is_manual', models.BooleanField(default=False)),
                ('priority', models.IntegerField(default=0)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user_profile', models.ForeignKey(...)),
                ('assigned_by', models.ForeignKey(...)),
            ],
            options={
                'unique_together': [['user_profile', 'category', 'is_active']],
                'ordering': ['priority', '-assigned_at'],
            },
        ),
    ]
```

**Action Items:**
- [ ] Choose migration approach (A or B)
- [ ] Create migration file
- [ ] Test migration on dev database
- [ ] Review migration SQL

---

#### **Step 2.2: Run Migration**
```bash
# On dev environment
python manage.py makemigrations
python manage.py migrate --plan
python manage.py migrate
```

**Action Items:**
- [ ] Run on dev database
- [ ] Verify schema changes
- [ ] Test queries work
- [ ] Backup database before migration

---

### **Phase 3: Data Migration (Day 3)**

#### **Step 3.1: Assign BOG/Leadership Members**
```python
# management/commands/assign_bog_leadership.py

def assign_bog_leadership():
    BOG_MEMBERS = [
        'amanda_towe',  # Verify username
        'cmaghas',      # Chris Maghas
        'tirimba_obonyo',
    ]
    
    for username in BOG_MEMBERS:
        try:
            user = User.objects.get(username=username)
            profile = user.profile
            
            # Option A: Set flag
            profile.team_category = 'bog_leadership'
            profile.is_manually_assigned = True
            profile.team_priority = 100  # Highest priority
            profile.save()
            
            # Option B: Create TeamAssignment
            TeamAssignment.objects.update_or_create(
                user_profile=profile,
                category='bog_leadership',
                defaults={
                    'is_manual': True,
                    'priority': 100,
                    'is_active': True,
                }
            )
            
            print(f"✅ Assigned {user.get_full_name()} to BOG/Leadership")
        except User.DoesNotExist:
            print(f"❌ User {username} not found")
```

**Action Items:**
- [ ] Run assignment script
- [ ] Verify assignments
- [ ] Test display on page

---

#### **Step 3.2: Assign Elite Team Member**
```python
def assign_elite_team():
    ELITE_MEMBER = 'coda-info'  # Verify username
    
    try:
        user = User.objects.get(username=ELITE_MEMBER)
        profile = user.profile
        
        profile.team_category = 'elite'
        profile.is_manually_assigned = True
        profile.team_priority = 90
        profile.save()
        
        print(f"✅ Assigned {user.get_full_name()} to Elite Team")
    except User.DoesNotExist:
        print(f"❌ User {ELITE_MEMBER} not found")
```

**Action Items:**
- [ ] Verify username `coda-info` exists
- [ ] Run assignment script
- [ ] Verify assignment

---

#### **Step 3.3: Verify Lead Team Members**
```python
def verify_lead_team():
    LEAD_TEAM_MEMBERS = [
        'edwin_kimtai',
        'emanuel_masakhwe',
        'george_ndahiro',
    ]
    
    for username in LEAD_TEAM_MEMBERS:
        user = User.objects.get(username=username)
        profile = user.profile
        
        # Calculate current points
        points = calculate_current_points(profile)
        
        # Check if they qualify by points
        if points >= 8000:
            print(f"✅ {user.get_full_name()}: {points} points (Qualifies)")
        else:
            print(f"⚠️ {user.get_full_name()}: {points} points (Needs manual assignment)")
            # Assign manually if needed
            profile.team_category = 'lead'
            profile.is_manually_assigned = True
            profile.save()
```

**Action Items:**
- [ ] Run verification script
- [ ] Manually assign if points insufficient
- [ ] Set priorities

---

#### **Step 3.4: Assign Support Team Members**
```python
def assign_support_team():
    SUPPORT_MEMBERS = [
        'hashim_kha',
        'christine_karagu',
    ]
    
    for username in SUPPORT_MEMBERS:
        user = User.objects.get(username=username)
        profile = user.profile
        
        # Verify they're contractors (sub_category=2)
        if user.sub_category == 2:
            points = calculate_current_points(profile)
            if points >= 1000:
                print(f"✅ {user.get_full_name()}: {points} points (Qualifies)")
            else:
                # Assign manually
                profile.team_category = 'support'
                profile.is_manually_assigned = True
                profile.save()
        else:
            print(f"⚠️ {user.get_full_name()} is not a contractor")
```

**Action Items:**
- [ ] Run assignment script
- [ ] Verify contractor status
- [ ] Assign manually if needed

---

#### **Step 3.5: Verify Other Team Members**
```python
def verify_other_teams():
    TEAMS = {
        'senior_analyst': ['sylvia_jelante'],
        'junior_analyst': ['phinehas_maina'],
        'senior_trainee': ['bonie_luke', 'brenda_nasimiyu'],
        'junior_trainee': ['angel', 'eugene'],
    }
    
    POINT_RANGES = {
        'senior_analyst': (7000, 8000),
        'junior_analyst': (6000, 7000),
        'senior_trainee': (5000, 6000),
        'junior_trainee': (4000, 5000),
    }
    
    for category, usernames in TEAMS.items():
        min_points, max_points = POINT_RANGES[category]
        
        for username in usernames:
            user = User.objects.get(username=username)
            profile = user.profile
            points = calculate_current_points(profile)
            
            if min_points <= points <= max_points:
                print(f"✅ {user.get_full_name()}: {points} points (Qualifies)")
            else:
                print(f"⚠️ {user.get_full_name()}: {points} points (Needs manual assignment)")
                profile.team_category = category
                profile.is_manually_assigned = True
                profile.save()
```

**Action Items:**
- [ ] Run verification script
- [ ] Manually assign if needed
- [ ] Set priorities

---

### **Phase 4: Code Updates (Day 4-5)**

#### **Step 4.1: Update Team View Logic**
```python
# coda/main/views.py

def team(request, title):
    # Get manual assignments first
    manual_assignments = UserProfile.objects.filter(
        is_manually_assigned=True,
        team_category__isnull=False
    ).order_by('team_priority', 'user__date_joined')
    
    # Group by category
    team_categories = {}
    for assignment in manual_assignments:
        category = assignment.team_category
        if category not in team_categories:
            team_categories[category] = []
        team_categories[category].append(assignment)
    
    # Get points-based assignments (if not manually assigned)
    points_based = UserProfile.objects.filter(
        is_manually_assigned=False,
        user__category=2,
        user__is_active=True
    ).annotate(
        total_points=F('total_points')  # Use cached field
    )
    
    # Categorize by points
    for profile in points_based:
        category = get_category_from_points(profile.total_points)
        if category not in team_categories:
            team_categories[category] = []
        team_categories[category].append(profile)
    
    # Build context
    context = {
        'team_categories': team_categories,
        'title': get_heading_for_page(title),
    }
    
    return render(request, 'main/team_profiles.html', context)
```

**Action Items:**
- [ ] Update view logic
- [ ] Test with new data
- [ ] Verify all categories display

---

#### **Step 4.2: Remove Hardcoded Logic**
```python
# Remove this:
elite_team_member = UserProfile.objects.filter(
    user__is_superuser=True, 
    user__username='c_maghas'  # ❌ Remove
)

# Replace with:
elite_team = UserProfile.objects.filter(
    team_category='elite',
    is_manually_assigned=True
).order_by('team_priority')
```

**Action Items:**
- [ ] Find all hardcoded usernames
- [ ] Replace with category-based logic
- [ ] Test thoroughly

---

#### **Step 4.3: Fix Typo**
```python
# Change:
elementry = list(filter(...))

# To:
elementary = list(filter(...))
```

**Action Items:**
- [ ] Find all instances of "elementry"
- [ ] Replace with "elementary"
- [ ] Update variable names

---

### **Phase 5: Point Calculation Update (Day 6)**

#### **Step 5.1: Create Management Command**
```python
# management/commands/recalculate_team_points.py

from django.core.management.base import BaseCommand
from accounts.models import UserProfile
from main.services.team_service import TeamService

class Command(BaseCommand):
    help = 'Recalculate and cache team member points'
    
    def handle(self, *args, **options):
        self.stdout.write('Calculating team points...')
        
        profiles = UserProfile.objects.filter(
            user__category=2,
            user__is_active=True
        )
        
        for profile in profiles:
            points = TeamService.calculate_total_points(profile)
            profile.total_points = points
            profile.total_points_calculated_at = timezone.now()
            profile.save()
            
            self.stdout.write(
                f"✅ {profile.user.get_full_name()}: {points} points"
            )
        
        self.stdout.write(self.style.SUCCESS('Points calculation complete'))
```

**Action Items:**
- [ ] Create management command
- [ ] Test on dev database
- [ ] Schedule daily cron job

---

#### **Step 5.2: Schedule Daily Job**
```python
# Add to crontab or Celery beat

# Daily at 2 AM
0 2 * * * cd /app && python manage.py recalculate_team_points
```

**Action Items:**
- [ ] Set up cron job
- [ ] Test execution
- [ ] Monitor logs

---

### **Phase 6: Testing (Day 7)**

#### **Step 6.1: Manual Testing Checklist**
- [ ] Navigate to `/about/` - team section displays
- [ ] Navigate to `/members/team_profiles` - all categories show
- [ ] Verify BOG/Leadership shows 3 members
- [ ] Verify Elite Team shows 1 member
- [ ] Verify Lead Team shows 3 members
- [ ] Verify Support Team shows 2 members
- [ ] Verify Senior Analysts shows 1 member
- [ ] Verify Junior Analysts shows 1 member
- [ ] Verify Senior Trainee shows 2 members
- [ ] Verify Junior Trainee shows 2 members
- [ ] Test image loading
- [ ] Test description display
- [ ] Test admin view (points visible)
- [ ] Test non-admin view (points hidden)

---

#### **Step 6.2: Automated Testing**
```python
# tests/test_team_assignment.py

def test_bog_leadership_assignment():
    # Test BOG members are assigned correctly
    
def test_elite_team_assignment():
    # Test Elite team member is assigned
    
def test_lead_team_assignment():
    # Test Lead team members
    
# ... etc
```

**Action Items:**
- [ ] Write test cases
- [ ] Run test suite
- [ ] Fix any failures

---

### **Phase 7: Deployment (Day 8)**

#### **Step 7.1: Deploy to UAT**
```bash
# 1. Backup database
heroku pg:backups:capture --app codamakutano

# 2. Run migrations
heroku run "cd coda && python manage.py migrate" --app codamakutano

# 3. Run data migration
heroku run "cd coda && python manage.py assign_bog_leadership" --app codamakutano
heroku run "cd coda && python manage.py assign_elite_team" --app codamakutano
heroku run "cd coda && python manage.py verify_lead_team" --app codamakutano
# ... etc

# 4. Recalculate points
heroku run "cd coda && python manage.py recalculate_team_points" --app codamakutano

# 5. Test on UAT
```

**Action Items:**
- [ ] Deploy to UAT
- [ ] Test thoroughly
- [ ] Get stakeholder approval

---

#### **Step 7.2: Deploy to Production**
```bash
# Same steps as UAT, but on production
# Add extra verification steps
```

**Action Items:**
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Verify team display

---

## 🚨 ROLLBACK PLAN

### **If Issues Occur:**

1. **Revert Migration:**
```bash
python manage.py migrate accounts XXXX_previous_migration
```

2. **Restore Database:**
```bash
heroku pg:backups:restore BACKUP_ID --app codamakutano
```

3. **Revert Code:**
```bash
git revert HEAD
git push heroku main
```

---

## ✅ MIGRATION CHECKLIST

### **Pre-Migration:**
- [ ] Backup database
- [ ] Review migration plan
- [ ] Test on dev environment
- [ ] Get stakeholder approval

### **Migration:**
- [ ] Run data verification
- [ ] Create/update data model
- [ ] Run data migration scripts
- [ ] Update code
- [ ] Test thoroughly

### **Post-Migration:**
- [ ] Verify all team members display
- [ ] Verify categories correct
- [ ] Monitor performance
- [ ] Update documentation
- [ ] Train admin users

---

## 📝 NEXT STEPS

1. **Review migration plan** - Confirm approach
2. **Select data model option** - Choose A or B
3. **Review Document 6** - Implementation Guide
4. **Begin Phase 1** - Data verification

---

**Continue to Document 6: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)**

