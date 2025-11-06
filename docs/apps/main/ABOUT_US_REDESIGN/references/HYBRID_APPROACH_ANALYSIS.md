# HYBRID APPROACH - Manual + Points System

**Created:** November 5, 2025  
**Purpose:** Analysis of hybrid team assignment system

---

## 🎯 HYBRID SYSTEM DESIGN

### **Concept:**
- **Manual Assignment:** BOG/Leadership, Elite, Lead Team, Support, Senior Analysts, Junior Analysts
- **Points-Based:** Future Talents (Senior Trainee, Junior Trainee, Elementary)

### **Rationale:**
✅ **Senior roles** are strategic and should be manually controlled  
✅ **Junior roles** benefit from automated progression based on performance  
✅ **Best of both worlds** - control where needed, automation where beneficial

---

## 📊 SYSTEM BREAKDOWN

### **Manual Categories (6 categories)**

```python
MANUAL_CATEGORIES = [
    'bog_leadership',    # BOG/Leadership
    'elite',             # Elite Team
    'lead',              # Lead Team
    'support',           # Support Team
    'senior_analyst',    # Senior Analysts
    'junior_analyst',    # Junior Analysts
]

# Assignment method: Admin sets flags/fields
# Display order: By manual priority
# Changes: Manual admin updates
```

**Members:**
- BOG/Leadership: Amanda Towe, Chris Maghas (cmaghas), Tirimba Obonyo
- Elite: Chris Maghas (coda-info)
- Lead: Edwin Kimtai, Emanuel Masakhwe, George Ndahiro
- Support: Hashim Kha, Christine Karagu
- Senior Analysts: Sylvia Jelante
- Junior Analysts: Phinehas Maina

---

### **Points-Based Categories (3 categories)**

```python
POINTS_CATEGORIES = [
    'senior_trainee',    # Senior Trainee (5,000-6,000 points)
    'junior_trainee',    # Junior Trainee (4,000-5,000 points)
    'elementary',        # Elementary (<4,000 points)
]

# Assignment method: Automatic based on points
# Display order: By points (highest first)
# Changes: Daily point recalculation
```

**Current Members:**
- Senior Trainee: Bonie Luke, Brenda Nasimiyu
- Junior Trainee: Angel, Eugene

**Future Growth:**
- As trainees gain points, they auto-promote
- When they exceed Junior Analyst threshold (6,000+), admin manually promotes

---

## 🏗️ DATA MODEL DESIGN

### **Option 1: Simple Flag-Based (Recommended for Hybrid)** ⭐

```python
class UserProfile(models.Model):
    # Existing fields...
    user = OneToOneField(CustomerUser)
    position = CharField()
    description = TextField()
    
    # Manual assignment fields
    team_category_manual = CharField(
        max_length=50,
        choices=MANUAL_CATEGORIES,
        null=True,
        blank=True,
        help_text="Manual team category (overrides points)"
    )
    team_priority = IntegerField(
        default=0,
        help_text="Display priority within category"
    )
    is_manually_assigned = BooleanField(
        default=False,
        help_text="True = manual assignment, False = points-based"
    )
    
    # Cached points (for future talents)
    total_points = IntegerField(
        default=0,
        db_index=True,
        help_text="Cached total points (recalculated daily)"
    )
    total_points_calculated_at = DateTimeField(
        null=True,
        blank=True
    )
    
    # Metadata
    last_promoted = DateTimeField(null=True, blank=True)
    promotion_notes = TextField(blank=True)
    
    def get_team_category(self):
        """Get team category (manual takes precedence)"""
        if self.is_manually_assigned and self.team_category_manual:
            return self.team_category_manual
        else:
            # Points-based categorization
            return self._category_from_points()
    
    def _category_from_points(self):
        """Calculate category from points (for future talents)"""
        if self.total_points >= 6000:
            # Eligible for manual promotion to Junior Analyst
            return 'ready_for_promotion'  # Special flag
        elif self.total_points >= 5000:
            return 'senior_trainee'
        elif self.total_points >= 4000:
            return 'junior_trainee'
        else:
            return 'elementary'
```

**Database Schema:**
```sql
ALTER TABLE accounts_userprofile
ADD COLUMN team_category_manual VARCHAR(50) NULL,
ADD COLUMN team_priority INTEGER DEFAULT 0,
ADD COLUMN is_manually_assigned BOOLEAN DEFAULT FALSE,
ADD COLUMN total_points INTEGER DEFAULT 0,
ADD COLUMN total_points_calculated_at TIMESTAMP NULL,
ADD COLUMN last_promoted TIMESTAMP NULL,
ADD COLUMN promotion_notes TEXT;

CREATE INDEX idx_team_manual ON accounts_userprofile(is_manually_assigned, team_category_manual);
CREATE INDEX idx_team_points ON accounts_userprofile(total_points);
CREATE INDEX idx_team_priority ON accounts_userprofile(team_priority);
```

---

## 💻 IMPLEMENTATION CODE

### **1. Team Service**

```python
# coda/main/services/team_service.py

class TeamService:
    MANUAL_CATEGORIES = [
        'bog_leadership',
        'elite',
        'lead',
        'support',
        'senior_analyst',
        'junior_analyst',
    ]
    
    POINTS_CATEGORIES = [
        'senior_trainee',
        'junior_trainee',
        'elementary',
    ]
    
    POINT_THRESHOLDS = {
        'senior_trainee': (5000, 6000),
        'junior_trainee': (4000, 5000),
        'elementary': (0, 4000),
    }
    
    @staticmethod
    def get_team_members_by_category(category):
        """
        Get team members for a category.
        Returns different logic based on category type.
        """
        if category in TeamService.MANUAL_CATEGORIES:
            # Manual assignment - filter by flag
            return UserProfile.objects.filter(
                is_manually_assigned=True,
                team_category_manual=category,
                user__is_active=True
            ).select_related('user').order_by(
                'team_priority',
                'user__date_joined'
            )
        
        elif category in TeamService.POINTS_CATEGORIES:
            # Points-based - filter by point range
            min_points, max_points = TeamService.POINT_THRESHOLDS[category]
            
            return UserProfile.objects.filter(
                is_manually_assigned=False,  # Only points-based
                total_points__gte=min_points,
                total_points__lt=max_points,
                user__is_active=True
            ).select_related('user').order_by(
                '-total_points',  # Highest points first
                'user__date_joined'
            )
        
        else:
            return UserProfile.objects.none()
    
    @staticmethod
    def get_promotion_candidates():
        """
        Get trainees ready for manual promotion to Junior Analyst.
        Returns members with 6,000+ points who aren't manually assigned.
        """
        return UserProfile.objects.filter(
            is_manually_assigned=False,
            total_points__gte=6000,
            user__is_active=True
        ).select_related('user').order_by('-total_points')
    
    @staticmethod
    def promote_to_manual_category(user_profile, category, priority=0, notes=''):
        """
        Manually promote a team member to a manual category.
        """
        user_profile.is_manually_assigned = True
        user_profile.team_category_manual = category
        user_profile.team_priority = priority
        user_profile.last_promoted = timezone.now()
        user_profile.promotion_notes = notes
        user_profile.save()
        
        # Log promotion
        logger.info(
            f"Promoted {user_profile.user.get_full_name()} "
            f"to {category} with {user_profile.total_points} points"
        )
    
    @staticmethod
    def calculate_total_points(user_profile):
        """Calculate total points (for future talents)"""
        education_points = TeamService._calculate_education_points(user_profile)
        task_points = TeamService._calculate_task_points(user_profile)
        requirement_points = TeamService._calculate_requirement_points(user_profile)
        training_points = TeamService._calculate_training_points(user_profile)
        assessment_points = TeamService._calculate_assessment_points(user_profile)
        
        return (
            education_points +
            task_points +
            requirement_points +
            training_points +
            assessment_points
        )
    
    @staticmethod
    def _calculate_education_points(user_profile):
        """Education points (same as before)"""
        EDUCATION_MULTIPLIERS = {
            1: 250,    # High School
            2: 500,    # Some College
            3: 1000,   # Bachelor's
            4: 1500,   # Master's
            5: 2000,   # Doctorate
        }
        return EDUCATION_MULTIPLIERS.get(user_profile.education, 0)
    
    @staticmethod
    def _calculate_task_points(user_profile):
        """Task history points"""
        from management.models import TaskHistory
        return TaskHistory.objects.filter(
            employee_id=user_profile.user
        ).aggregate(
            total=Sum('point')
        )['total'] or 0
    
    @staticmethod
    def _calculate_requirement_points(user_profile):
        """Requirement points (duration)"""
        from management.models import Requirement
        return Requirement.objects.filter(
            assigned_to=user_profile.user
        ).aggregate(
            total=Sum('duration')
        )['total'] or 0
    
    @staticmethod
    def _calculate_training_points(user_profile):
        """Training points"""
        from management.models import Training
        
        trainings = Training.objects.filter(presenter=user_profile.user)
        total = 0
        for training in trainings:
            multiplier = {
                1: 5,
                2: 10,
                3: 15,
                4: 20,
                5: 25,
            }.get(training.level, 0)
            total += training.level * multiplier
        
        return total
    
    @staticmethod
    def _calculate_assessment_points(user_profile):
        """Client assessment points"""
        from professional_services.models import ClientAssessment
        
        latest = ClientAssessment.objects.filter(
            email=user_profile.user.email
        ).order_by('-rating_date').first()
        
        return latest.totalpoints if latest else 0
```

---

### **2. Updated Team View**

```python
# coda/main/views.py

def team(request, title):
    """Main team view with hybrid assignment"""
    
    # Define categories for each page
    if title == 'team_profiles':
        # Established team members (manual)
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
        # Future talents (points-based)
        categories = [
            ('senior_trainee', 'Senior Trainee Team'),
            ('junior_trainee', 'Junior Trainee Team'),
            ('elementary', 'Elementary'),
        ]
        heading = "MINDS OF TOMORROW: LEADING DATA ANALYTICS AND WEB DEVELOPMENT"
        
    elif title == 'board':
        categories = [
            ('bog_leadership', 'Board of Governors'),
        ]
        heading = "THE BOG"
        
    else:
        categories = []
        heading = "TEAM"
    
    # Get team members for each category
    team_categories = {}
    for category_slug, category_name in categories:
        members = TeamService.get_team_members_by_category(category_slug)
        if members:
            team_categories[category_name] = members
    
    # Get promotion candidates (if admin)
    promotion_candidates = []
    if request.user.is_staff:
        promotion_candidates = TeamService.get_promotion_candidates()
    
    # Get category descriptions
    team_member_descriptions = {}
    for category_slug, category_name in categories:
        try:
            desc = Team_Members.objects.get(
                category=category_slug
            ).description
            team_member_descriptions[category_name] = desc
        except Team_Members.DoesNotExist:
            team_member_descriptions[category_name] = ""
    
    context = {
        'team_categories': team_categories,
        'team_member_descriptions': team_member_descriptions,
        'promotion_candidates': promotion_candidates,
        'title': heading,
    }
    
    return render(request, 'main/team_profiles.html', context)
```

---

### **3. Management Commands**

#### **3.1 Assign Manual Categories**

```python
# management/commands/assign_manual_team_members.py

from django.core.management.base import BaseCommand
from accounts.models import UserProfile, CustomerUser

class Command(BaseCommand):
    help = 'Assign team members to manual categories'
    
    MANUAL_ASSIGNMENTS = {
        'bog_leadership': [
            ('amanda_towe', 'Amanda Towe', 100),
            ('cmaghas', 'Chris Maghas', 90),
            ('tirimba_obonyo', 'Tirimba Obonyo', 80),
        ],
        'elite': [
            ('coda-info', 'Chris Maghas', 100),
        ],
        'lead': [
            ('edwin_kimtai', 'Edwin Kimtai', 100),
            ('emanuel_masakhwe', 'Emanuel Masakhwe', 90),
            ('george_ndahiro', 'George Ndahiro', 80),
        ],
        'support': [
            ('hashim_kha', 'Hashim Kha', 100),
            ('christine_karagu', 'Christine Karagu', 90),
        ],
        'senior_analyst': [
            ('sylvia_jelante', 'Sylvia Jelante', 100),
        ],
        'junior_analyst': [
            ('phinehas_maina', 'Phinehas Maina', 100),
        ],
    }
    
    def handle(self, *args, **options):
        self.stdout.write('Assigning manual team categories...\n')
        
        for category, members in self.MANUAL_ASSIGNMENTS.items():
            self.stdout.write(f"\n{category.upper()}:")
            
            for username, full_name, priority in members:
                try:
                    user = CustomerUser.objects.get(username=username)
                    profile = user.profile
                    
                    profile.is_manually_assigned = True
                    profile.team_category_manual = category
                    profile.team_priority = priority
                    profile.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ {full_name} ({username}) → {category} (priority: {priority})"
                        )
                    )
                    
                except CustomerUser.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ {full_name} ({username}) - USER NOT FOUND"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ {full_name} ({username}) - ERROR: {str(e)}"
                        )
                    )
        
        self.stdout.write(self.style.SUCCESS('\nManual assignments complete!'))
```

#### **3.2 Recalculate Points (Future Talents)**

```python
# management/commands/recalculate_team_points.py

from django.core.management.base import BaseCommand
from accounts.models import UserProfile
from main.services.team_service import TeamService
from django.utils import timezone

class Command(BaseCommand):
    help = 'Recalculate points for future talent team members'
    
    def handle(self, *args, **options):
        self.stdout.write('Recalculating points for future talents...\n')
        
        # Get all non-manually assigned profiles
        profiles = UserProfile.objects.filter(
            is_manually_assigned=False,
            user__category=2,  # Employee category
            user__is_active=True
        )
        
        total_updated = 0
        promotion_ready = []
        
        for profile in profiles:
            old_points = profile.total_points
            new_points = TeamService.calculate_total_points(profile)
            
            profile.total_points = new_points
            profile.total_points_calculated_at = timezone.now()
            profile.save()
            
            total_updated += 1
            
            # Check if ready for promotion
            if new_points >= 6000:
                promotion_ready.append((profile, new_points))
            
            # Determine category
            if new_points >= 5000:
                category = 'senior_trainee'
            elif new_points >= 4000:
                category = 'junior_trainee'
            else:
                category = 'elementary'
            
            change_indicator = ''
            if new_points > old_points:
                change_indicator = f'(↑ +{new_points - old_points})'
            elif new_points < old_points:
                change_indicator = f'(↓ -{old_points - new_points})'
            
            self.stdout.write(
                f"  {profile.user.get_full_name():30} "
                f"{new_points:5} points {change_indicator:15} → {category}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Updated {total_updated} team members'
            )
        )
        
        # Show promotion candidates
        if promotion_ready:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️ {len(promotion_ready)} members ready for manual promotion:'
                )
            )
            for profile, points in promotion_ready:
                self.stdout.write(
                    f"  • {profile.user.get_full_name()} ({points} points) "
                    f"- Ready for Junior Analyst"
                )
```

#### **3.3 Show Promotion Candidates**

```python
# management/commands/show_promotion_candidates.py

from django.core.management.base import BaseCommand
from main.services.team_service import TeamService

class Command(BaseCommand):
    help = 'Show team members ready for promotion'
    
    def handle(self, *args, **options):
        candidates = TeamService.get_promotion_candidates()
        
        if not candidates:
            self.stdout.write(
                self.style.SUCCESS('No promotion candidates at this time.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'\n🎯 {len(candidates)} members ready for manual promotion to Junior Analyst:\n'
            )
        )
        
        for profile in candidates:
            self.stdout.write(
                f"  {profile.user.get_full_name():30} "
                f"{profile.total_points:5} points "
                f"({profile.user.email})"
            )
        
        self.stdout.write(
            '\nTo promote, use:\n'
            '  python manage.py promote_team_member <username> junior_analyst\n'
        )
```

---

## 📋 MIGRATION PLAN

### **Phase 1: Database Changes**

```bash
# Create migration
python manage.py makemigrations accounts --name add_hybrid_team_fields

# Review migration
python manage.py migrate --plan

# Run migration
python manage.py migrate
```

### **Phase 2: Assign Manual Categories**

```bash
# Assign all manual team members
python manage.py assign_manual_team_members

# Verify assignments
python manage.py shell
>>> from accounts.models import UserProfile
>>> UserProfile.objects.filter(is_manually_assigned=True).count()
# Should be 10 (3 BOG + 1 Elite + 3 Lead + 2 Support + 1 Senior + 1 Junior)
```

### **Phase 3: Calculate Points for Future Talents**

```bash
# Calculate points
python manage.py recalculate_team_points

# Check promotion candidates
python manage.py show_promotion_candidates
```

### **Phase 4: Update View Logic**

Replace existing `team()` view with hybrid version above.

### **Phase 5: Test**

```bash
# Test manual categories display
curl http://localhost:8000/members/team_profiles

# Test future talents display
curl http://localhost:8000/members/future_talents

# Test admin sees promotion candidates
# Login as admin, visit /members/team_profiles
```

---

## ✅ ADVANTAGES

### **1. Best of Both Worlds**
- ✅ Control for strategic roles (BOG, Elite, Lead)
- ✅ Automation for development roles (Trainees)
- ✅ Clear progression path for juniors

### **2. Simple Logic**
- ✅ One flag determines assignment type (`is_manually_assigned`)
- ✅ Clear separation between manual and points-based
- ✅ Easy to understand and maintain

### **3. Flexible Promotion**
- ✅ Trainees auto-categorize by points
- ✅ Admin manually promotes when ready (6,000+ points)
- ✅ Promotion candidates automatically flagged

### **4. Performance**
- ✅ Cached points (no calculation on page load)
- ✅ Simple queries (indexed fields)
- ✅ Fast page loads

### **5. Maintainability**
- ✅ Single data model (UserProfile)
- ✅ Clear business logic
- ✅ Easy to extend

---

## ⚠️ CHALLENGES & SOLUTIONS

### **Challenge 1: Two Logic Paths**

**Problem:** Code needs to handle both manual and points-based

**Solution:**
```python
def get_team_category(self):
    if self.is_manually_assigned:
        return self.team_category_manual
    else:
        return self._category_from_points()
```

**Impact:** Minimal - clean separation

---

### **Challenge 2: Promotion Threshold**

**Problem:** When do trainees get manually promoted?

**Solution:**
- Auto-flag at 6,000+ points
- Admin reviews candidates
- Manual promotion to Junior Analyst
- Clear promotion criteria documented

**Process:**
```
Trainee reaches 6,000 points
  ↓
System flags as "ready for promotion"
  ↓
Admin reviews (skills, projects, behavior)
  ↓
Admin manually promotes to Junior Analyst
  ↓
Now in manual category
```

---

### **Challenge 3: Point Calculation for Manual Members**

**Problem:** Should manually assigned members still have points calculated?

**Solution:** Yes, but not used for categorization

```python
# Calculate points for everyone
python manage.py recalculate_team_points --all

# But only use for display/reference, not categorization
# Manual members stay in their assigned category
```

**Benefit:** Can still track performance even for manual members

---

### **Challenge 4: Category Changes**

**Problem:** What if a manually assigned member's points drop?

**Solution:** Manual assignment takes precedence

```python
# Scenario: Lead Team member's points drop to 5,000
# They stay in Lead Team (manual assignment)
# Admin can demote if needed

# To demote:
profile.is_manually_assigned = False
profile.team_category_manual = None
profile.save()
# Now they'll be auto-categorized by points (Senior Trainee)
```

**Decision:** Manual assignments are sticky (don't auto-demote)

---

### **Challenge 5: Testing Both Systems**

**Problem:** Need to test manual and points-based logic

**Solution:**
```python
# tests/test_hybrid_team.py

def test_manual_assignment_takes_precedence():
    """Test manual assignment overrides points"""
    profile = UserProfile.objects.create(...)
    profile.total_points = 3000  # Would be junior_trainee
    profile.is_manually_assigned = True
    profile.team_category_manual = 'lead'
    
    assert profile.get_team_category() == 'lead'

def test_points_based_categorization():
    """Test points-based for non-manual"""
    profile = UserProfile.objects.create(...)
    profile.total_points = 5500
    profile.is_manually_assigned = False
    
    assert profile.get_team_category() == 'senior_trainee'

def test_promotion_candidates():
    """Test 6000+ points flagged for promotion"""
    profile = UserProfile.objects.create(...)
    profile.total_points = 6500
    profile.is_manually_assigned = False
    
    candidates = TeamService.get_promotion_candidates()
    assert profile in candidates
```

---

### **Challenge 6: Admin Interface**

**Problem:** Admin needs UI to manage both systems

**Solution:**
```python
# admin.py

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'get_team_category',
        'is_manually_assigned',
        'total_points',
        'team_priority',
    ]
    list_filter = [
        'is_manually_assigned',
        'team_category_manual',
    ]
    search_fields = ['user__username', 'user__email']
    
    fieldsets = [
        ('User Info', {
            'fields': ['user', 'position', 'description']
        }),
        ('Team Assignment', {
            'fields': [
                'is_manually_assigned',
                'team_category_manual',
                'team_priority',
                'total_points',
                'total_points_calculated_at',
            ]
        }),
        ('Promotion', {
            'fields': [
                'last_promoted',
                'promotion_notes',
            ]
        }),
    ]
    
    actions = ['promote_to_junior_analyst', 'recalculate_points']
    
    def promote_to_junior_analyst(self, request, queryset):
        for profile in queryset:
            TeamService.promote_to_manual_category(
                profile,
                'junior_analyst',
                priority=50,
                notes=f'Promoted by {request.user.username}'
            )
        self.message_user(request, f'Promoted {queryset.count()} members')
    
    def recalculate_points(self, request, queryset):
        for profile in queryset:
            profile.total_points = TeamService.calculate_total_points(profile)
            profile.save()
        self.message_user(request, f'Recalculated points for {queryset.count()} members')
```

---

### **Challenge 7: Performance (Points Calculation)**

**Problem:** Daily point calculation for all members

**Solution:** Cron job + selective calculation

```bash
# Crontab - Daily at 2 AM
0 2 * * * cd /app && python manage.py recalculate_team_points

# Only calculate for non-manual (faster)
# Manual members can be calculated weekly or on-demand
```

**Optimization:**
```python
# Only calculate for future talents (not manual)
profiles = UserProfile.objects.filter(
    is_manually_assigned=False  # Only points-based
)
# Much faster - only 10-20 profiles vs 40+
```

---

### **Challenge 8: Data Migration**

**Problem:** Existing team members need categorization

**Solution:** Migration script

```python
# One-time migration

# Step 1: Set all current members as manual
UserProfile.objects.filter(
    user__category=2,
    user__is_active=True
).update(
    is_manually_assigned=True
)

# Step 2: Assign categories based on current logic
# (Run assign_manual_team_members.py)

# Step 3: Identify future talents (trainees)
# Mark them as points-based
UserProfile.objects.filter(
    user__username__in=['bonie_luke', 'brenda_nasimiyu', 'angel', 'eugene']
).update(
    is_manually_assigned=False,
    team_category_manual=None
)

# Step 4: Calculate initial points
python manage.py recalculate_team_points
```

---

## 📊 COMPARISON: Pure Manual vs Pure Points vs Hybrid

| Aspect | Pure Manual | Pure Points | **Hybrid** ⭐ |
|--------|-------------|-------------|---------------|
| Control | ✅ Full | ❌ None | ✅ Where needed |
| Automation | ❌ None | ✅ Full | ✅ For juniors |
| Flexibility | ✅ High | ❌ Low | ✅ High |
| Maintenance | ❌ High | ✅ Low | ✅ Medium |
| Performance | ✅ Fast | ❌ Slow | ✅ Fast |
| Progression | ❌ Manual | ✅ Auto | ✅ Both |
| Complexity | ✅ Simple | ❌ Complex | ✅ Moderate |
| **Best For** | Established | All levels | **Real World** |

---

## 🎯 RECOMMENDED HYBRID CONFIGURATION

### **Manual Categories (Admin Controlled)**
```python
MANUAL_CATEGORIES = {
    'bog_leadership': {
        'name': 'BOG/Leadership',
        'description': 'Board of Governors and Leadership Team',
        'assignment': 'manual',
        'display_order': 1,
    },
    'elite': {
        'name': 'Elite Team',
        'description': 'Top performers with exceptional expertise',
        'assignment': 'manual',
        'display_order': 2,
    },
    'lead': {
        'name': 'Lead Team',
        'description': 'Team leaders and senior professionals',
        'assignment': 'manual',
        'display_order': 3,
    },
    'support': {
        'name': 'Support Team',
        'description': 'Contractor support specialists',
        'assignment': 'manual',
        'display_order': 4,
    },
    'senior_analyst': {
        'name': 'Senior Analysts',
        'description': 'Experienced data analysts',
        'assignment': 'manual',
        'display_order': 5,
    },
    'junior_analyst': {
        'name': 'Junior Analysts',
        'description': 'Entry-level analysts',
        'assignment': 'manual',
        'display_order': 6,
    },
}
```

### **Points-Based Categories (Auto Calculated)**
```python
POINTS_CATEGORIES = {
    'senior_trainee': {
        'name': 'Senior Trainee Team',
        'description': 'Advanced trainees (5,000-6,000 points)',
        'assignment': 'points',
        'point_range': (5000, 6000),
        'display_order': 7,
    },
    'junior_trainee': {
        'name': 'Junior Trainee Team',
        'description': 'Developing trainees (4,000-5,000 points)',
        'assignment': 'points',
        'point_range': (4000, 5000),
        'display_order': 8,
    },
    'elementary': {
        'name': 'Elementary',
        'description': 'New trainees (<4,000 points)',
        'assignment': 'points',
        'point_range': (0, 4000),
        'display_order': 9,
    },
}
```

### **Promotion Criteria**
```python
PROMOTION_CRITERIA = {
    'junior_trainee_to_senior_trainee': {
        'points_required': 5000,
        'type': 'automatic',
    },
    'senior_trainee_to_junior_analyst': {
        'points_required': 6000,
        'type': 'manual',  # Admin review required
        'review_criteria': [
            'Minimum 6,000 points',
            'Completed 3+ projects',
            'Positive peer reviews',
            'Manager recommendation',
        ],
    },
}
```

---

## ✅ FINAL RECOMMENDATION

**YES, the hybrid approach is not only doable but RECOMMENDED!**

### **Why Hybrid is Best:**

1. **Realistic** - Matches how organizations actually work
2. **Flexible** - Control where needed, automation where beneficial
3. **Scalable** - Can handle growth in future talents
4. **Performant** - Cached points, simple queries
5. **Maintainable** - Clear logic, well-separated concerns

### **Implementation Effort:**
- **Low to Medium** (3-5 days)
- Simpler than pure points system
- More flexible than pure manual

### **Challenges:**
- **Minor** - Well-understood solutions
- Two logic paths (easily managed)
- Promotion criteria (clearly documented)
- Testing both systems (straightforward)

---

## 📝 NEXT STEPS

1. **Review this hybrid approach** - Confirm it meets your needs
2. **Run migration** - Add fields to UserProfile
3. **Assign manual categories** - Run management command
4. **Calculate points** - Run point calculation for trainees
5. **Update views** - Implement hybrid logic
6. **Test thoroughly** - Both manual and points-based
7. **Deploy** - UAT first, then production

---

**This hybrid approach gives you the best of both worlds! Ready to implement?**

