# Team Assignment System - Architecture

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 🏗️ Architecture Designed

---

## 🏗️ System Architecture

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  Views → Templates → Static Assets                          │
├─────────────────────────────────────────────────────────────┤
│  • team(request, title) - Main team view                    │
│  • about(request) - About page with team preview            │
│  • team_profiles.html - Team display template               │
│  • team_card.html - Individual member cards                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                      │
│  Services → Managers → Utilities                            │
├─────────────────────────────────────────────────────────────┤
│  • TeamService - Point calculation, categorization          │
│  • TeamAssignmentService - Group assignment logic           │
│  • PromotionService - Candidate detection, promotion        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                        │
│  Models → Django Groups → QuerySets                         │
├─────────────────────────────────────────────────────────────┤
│  • User (Django built-in)                                   │
│  • UserProfile (existing, NO CHANGES)                       │
│  • TeamProfile (NEW - 5 fields)                            │
│  • Group (Django built-in)                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA STORAGE LAYER                        │
│  PostgreSQL → Redis Cache → Google Drive                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema Design

### **New TeamProfile Model**

```python
class TeamProfile(models.Model):
    """
    Team-specific metadata. Category stored in Django Groups.
    
    Design Decision: Keep this model SMALL (5 fields only).
    Category assignment handled by Django's Group model.
    """
    
    # Core relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='team_profile',
        help_text='User this team profile belongs to'
    )
    
    # Display priority (for ordering within category)
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Display priority (higher = shown first)'
    )
    
    # Cached points (for auto-categorization)
    total_points = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Cached total points (recalculated daily)'
    )
    
    # Assignment method
    is_manually_assigned = models.BooleanField(
        default=False,
        db_index=True,
        help_text='True = manual assignment, False = points-based'
    )
    
    # Promotion tracking
    last_promoted = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When last promoted to manual category'
    )
    
    promotion_notes = models.TextField(
        blank=True,
        help_text='Promotion notes (who, why, when)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_teamprofile'
        verbose_name = 'Team Profile'
        verbose_name_plural = 'Team Profiles'
        indexes = [
            models.Index(fields=['priority', '-total_points']),
            models.Index(fields=['is_manually_assigned']),
            models.Index(fields=['total_points']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_category()}"
    
    @property
    def category(self):
        """Get team category from user's groups"""
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
        
        for group_name in TEAM_GROUPS:
            if self.user.groups.filter(name=group_name).exists():
                return group_name
        
        return None
    
    @property
    def category_slug(self):
        """Get category slug for URL/template use"""
        category_map = {
            'BOG/Leadership': 'bog_leadership',
            'Elite Team': 'elite',
            'Lead Team': 'lead',
            'Support Team': 'support',
            'Senior Analysts': 'senior_analyst',
            'Junior Analysts': 'junior_analyst',
            'Senior Trainee': 'senior_trainee',
            'Junior Trainee': 'junior_trainee',
            'Elementary': 'elementary',
        }
        return category_map.get(self.category, 'unknown')
```

**Table Structure:**
```sql
CREATE TABLE accounts_teamprofile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    is_manually_assigned BOOLEAN DEFAULT FALSE,
    last_promoted TIMESTAMP NULL,
    promotion_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_team_priority ON accounts_teamprofile(priority, total_points DESC);
CREATE INDEX idx_team_manual ON accounts_teamprofile(is_manually_assigned);
CREATE INDEX idx_team_points ON accounts_teamprofile(total_points);
```

**Size:** Small (5 data fields + 2 timestamps + 3 indexes)

---

### **Django Groups (Built-in, No Changes)**

```python
# Uses Django's existing Group model
from django.contrib.auth.models import Group

# Group model structure (Django built-in):
class Group(models.Model):
    name = CharField(max_length=150, unique=True)
    permissions = ManyToManyField(Permission)
```

**Team Groups to Create:**
```python
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
```

---

### **UserProfile Model (NO CHANGES!)**

```python
class UserProfile(models.Model):
    """
    NO CHANGES TO THIS MODEL!
    
    Team assignment handled by:
    - Django Groups (category)
    - TeamProfile (metadata)
    
    This keeps UserProfile at 38 fields. ✅
    """
    # ... existing 38 fields ...
    # NO team-related fields added!
```

---

## 🔄 Data Flow Architecture

### **Team Member Assignment Flow**

```
Admin Action: Assign Team Member
         │
         ▼
┌────────────────────────────┐
│ assign_team_member()       │
│ (Service Layer)            │
└────────────┬───────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐      ┌──────────────┐
│ Groups  │      │ TeamProfile  │
│ Table   │      │ Table        │
├─────────┤      ├──────────────┤
│ Add user│      │ priority: 100│
│ to group│      │ is_manual: T │
│ 'Lead'  │      │ promoted: now│
└─────────┘      └──────────────┘
```

### **Points Calculation Flow**

```
Cron Job (Daily 2 AM)
         │
         ▼
┌────────────────────────────┐
│ recalculate_team_points    │
│ (Management Command)       │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ For each non-manual member │
└────────────┬───────────────┘
             │
    ┌────────┴────────────────────────┐
    │                                 │
    ▼                                 ▼
┌─────────────┐           ┌─────────────────┐
│ Calculate:  │           │ Store in:       │
│ • Education │           │ TeamProfile     │
│ • Tasks     │           │ .total_points   │
│ • Reqs      │           │                 │
│ • Training  │           │ Update:         │
│ • Assessment│           │ .points_calc_at │
└─────────────┘           └─────────────────┘
             │
             ▼
┌────────────────────────────┐
│ Auto-assign to group:      │
│ • < 4K → Elementary        │
│ • 4-5K → Junior Trainee    │
│ • 5-6K → Senior Trainee    │
│ • ≥ 6K → Flag for promotion│
└────────────────────────────┘
```

### **Team Page Display Flow**

```
Request: /members/team_profiles
         │
         ▼
┌────────────────────────────┐
│ team(request, 'team')      │
│ (View)                     │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ For each category:         │
│ • BOG/Leadership           │
│ • Elite Team               │
│ • Lead Team                │
│ • etc...                   │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ Query members:             │
│                            │
│ User.objects.filter(       │
│   groups__name=category    │
│ ).select_related(          │
│   'profile',               │
│   'team_profile'           │
│ ).order_by(                │
│   'team_profile__priority',│
│   '-team_profile__points'  │
│ )                          │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│ Render template with data  │
└────────────────────────────┘

Total Queries: 1-2 per category × 9 categories = ~10 queries
(vs 100+ in old system)
```

---

## 🔧 Service Layer Architecture

### **TeamService**

```python
# coda/main/services/team_service.py

class TeamService:
    """
    Service layer for team operations.
    Handles point calculation, categorization, and queries.
    """
    
    MANUAL_CATEGORIES = [
        'BOG/Leadership',
        'Elite Team',
        'Lead Team',
        'Support Team',
        'Senior Analysts',
        'Junior Analysts',
    ]
    
    POINTS_CATEGORIES = [
        'Senior Trainee',
        'Junior Trainee',
        'Elementary',
    ]
    
    POINT_THRESHOLDS = {
        'Senior Trainee': (5000, 6000),
        'Junior Trainee': (4000, 5000),
        'Elementary': (0, 4000),
    }
    
    @staticmethod
    def get_team_members(category_name, use_priority=True):
        """
        Get all team members in a category.
        
        Args:
            category_name: Group name (e.g., 'Lead Team')
            use_priority: Whether to order by priority
        
        Returns:
            QuerySet of User objects with related data
        """
        queryset = User.objects.filter(
            groups__name=category_name,
            is_active=True
        ).select_related(
            'profile',
            'team_profile'
        )
        
        if use_priority:
            queryset = queryset.order_by(
                'team_profile__priority',
                '-team_profile__total_points',
                'date_joined'
            )
        
        return queryset
    
    @staticmethod
    def assign_to_category(user, category_name, priority=0, is_manual=True):
        """
        Assign user to team category.
        
        Args:
            user: User instance
            category_name: Group name
            priority: Display priority
            is_manual: Manual vs points-based
        """
        from django.contrib.auth.models import Group
        from django.utils import timezone
        
        # Get or create group
        group, created = Group.objects.get_or_create(name=category_name)
        
        # Clear existing team groups (only one team category)
        user.groups.filter(name__in=TeamService.ALL_CATEGORIES).delete()
        
        # Add to new group
        user.groups.add(group)
        
        # Update TeamProfile
        team_profile, created = TeamProfile.objects.get_or_create(user=user)
        team_profile.is_manually_assigned = is_manual
        team_profile.priority = priority
        team_profile.last_promoted = timezone.now()
        team_profile.save()
    
    @staticmethod
    def calculate_total_points(user):
        """
        Calculate total points from all sources.
        
        Returns: Integer total points
        """
        from management.models import TaskHistory, Requirement, Training
        from professional_services.models import ClientAssessment
        from django.db.models import Sum
        
        # 1. Education points
        profile = user.profile
        education_points = {
            1: 250, 2: 500, 3: 1000, 4: 1500, 5: 2000
        }.get(profile.education, 0)
        
        # 2. Task history points
        task_points = TaskHistory.objects.filter(
            employee_id=user
        ).aggregate(total=Sum('point'))['total'] or 0
        
        # 3. Requirement points (duration)
        requirement_points = Requirement.objects.filter(
            assigned_to=user
        ).aggregate(total=Sum('duration'))['total'] or 0
        
        # 4. Training points
        trainings = Training.objects.filter(presenter=user)
        training_points = 0
        for training in trainings:
            multiplier = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25}.get(training.level, 0)
            training_points += training.level * multiplier
        
        # 5. Client assessment points
        assessment = ClientAssessment.objects.filter(
            email=user.email
        ).order_by('-rating_date').first()
        assessment_points = assessment.totalpoints if assessment else 0
        
        return (
            education_points +
            task_points +
            requirement_points +
            training_points +
            assessment_points
        )
    
    @staticmethod
    def get_promotion_candidates():
        """Get trainees with 6,000+ points ready for promotion"""
        return User.objects.filter(
            team_profile__is_manually_assigned=False,
            team_profile__total_points__gte=6000,
            is_active=True
        ).select_related('profile', 'team_profile').order_by(
            '-team_profile__total_points'
        )
    
    @staticmethod
    def auto_categorize_by_points(user):
        """
        Auto-assign user to appropriate group based on points.
        Only for non-manually assigned members.
        """
        team_profile = user.team_profile
        
        if team_profile.is_manually_assigned:
            return  # Skip manual members
        
        points = team_profile.total_points
        
        # Determine category
        if points >= 5000:
            category = 'Senior Trainee'
        elif points >= 4000:
            category = 'Junior Trainee'
        else:
            category = 'Elementary'
        
        # Assign to group
        TeamService.assign_to_category(
            user,
            category,
            priority=0,
            is_manual=False
        )
```

---

## 🗄️ Database Relationships

```
┌──────────────────┐
│   auth_user      │
│  (Django built)  │
├──────────────────┤
│ PK: id           │
│ • username       │
│ • email          │
│ • first_name     │
│ • last_name      │
│ • is_active      │
└────┬─────────────┘
     │ 1
     │
     ├──────────────────────────────────────┐
     │                                      │
     │ has one                              │ has one
     │                                      │
     ▼ 1                                    ▼ 1
┌──────────────────┐              ┌──────────────────┐
│ UserProfile      │              │ TeamProfile      │
│ (NO CHANGES!)    │              │ (NEW!)           │
├──────────────────┤              ├──────────────────┤
│ PK: id           │              │ PK: id           │
│ FK: user_id      │              │ FK: user_id      │
│ • position       │              │ • priority       │
│ • description    │              │ • total_points   │
│ • education      │              │ • is_manual      │
│ • linkedin       │              │ • last_promoted  │
│ ... 38 fields    │              │ • notes          │
└──────────────────┘              └──────────────────┘
     
     │ belongs to many
     │
     ▼ *
┌──────────────────┐
│   auth_group     │
│  (Django built)  │
├──────────────────┤
│ PK: id           │
│ • name           │
├──────────────────┤
│ Values:          │
│ • BOG/Leadership │
│ • Elite Team     │
│ • Lead Team      │
│ • Support Team   │
│ • Senior Analyst │
│ • Junior Analyst │
│ • Senior Trainee │
│ • Junior Trainee │
│ • Elementary     │
└──────────────────┘

Relationship: Many-to-Many via auth_user_groups
```

---

## 🔀 Component Architecture

### **Views Layer**

```python
# coda/main/views.py

def team(request, title):
    """
    Main team view with Groups + TeamProfile.
    
    Simplified logic:
    1. Define categories for page
    2. Query users by group
    3. Order by priority/points
    4. Render template
    """
    categories = get_categories_for_page(title)
    
    team_categories = {}
    for category_name in categories:
        members = TeamService.get_team_members(category_name)
        if members.exists():
            team_categories[category_name] = members
    
    context = {
        'team_categories': team_categories,
        'title': get_heading(title),
    }
    
    return render(request, 'main/team_profiles.html', context)
```

**Query Count:** 1-2 queries per category (vs 5+ per member before)

---

### **Service Layer**

```python
# coda/main/services/team_service.py
class TeamService:
    # Point calculation
    # Category assignment
    # Group management
    # Promotion handling
```

---

### **Template Layer**

```html
<!-- team_profiles.html -->
{% for category_name, members in team_categories.items %}
    <h2>{{ category_name }}</h2>
    
    {% for user in members %}
        <div class="team-member-card">
            <img src="{{ user.profile.img_url }}" />
            <h3>{{ user.get_full_name }}</h3>
            <p>{{ user.profile.position }}</p>
            
            {% if request.user.is_staff %}
                <small>{{ user.team_profile.total_points }} points</small>
            {% endif %}
        </div>
    {% endfor %}
{% endfor %}
```

---

## 🔐 Security Architecture

### **Access Control**

| Action | Required Permission |
|--------|-------------------|
| View team pages | Public |
| View total points | is_staff=True |
| Assign to groups | is_superuser=True |
| Edit TeamProfile | is_superuser=True |
| Promote members | is_superuser=True |

### **Group Management Security**

```python
# Only superusers can manage groups
@user_passes_test(lambda u: u.is_superuser)
def assign_team_member(request):
    # Assignment logic
```

---

## 📈 Performance Architecture

### **Caching Strategy**

```python
# Layer 1: Page cache (1 hour)
@cache_page(60 * 60)
def team(request, title):
    # Entire page cached

# Layer 2: Database field cache
TeamProfile.total_points  # Updated daily, not calculated

# Layer 3: Query optimization
User.objects.filter(
    groups__name='Lead Team'
).select_related(
    'profile',
    'team_profile'
)  # 1 query with joins
```

### **Index Strategy**

```sql
-- TeamProfile indexes
CREATE INDEX idx_team_priority ON accounts_teamprofile(priority, total_points DESC);
CREATE INDEX idx_team_manual ON accounts_teamprofile(is_manually_assigned);
CREATE INDEX idx_team_points ON accounts_teamprofile(total_points);

-- Group indexes (Django built-in)
CREATE INDEX auth_group_name ON auth_group(name);

-- User-Group indexes (Django built-in)
CREATE INDEX auth_user_groups_user_id ON auth_user_groups(user_id);
CREATE INDEX auth_user_groups_group_id ON auth_user_groups(group_id);
```

---

## 🧪 Testing Architecture

### **Test Structure**

```
tests/
├── test_team_profile_model.py      # Model tests
├── test_team_service.py            # Service layer tests
├── test_team_views.py              # View tests
├── test_team_assignment.py         # Assignment logic tests
├── test_point_calculation.py       # Point calculation tests
└── test_promotion.py               # Promotion logic tests
```

### **Key Test Scenarios**

```python
# Model tests
- test_team_profile_creation
- test_category_property
- test_multiple_groups_handling

# Service tests
- test_calculate_points
- test_assign_to_category
- test_get_promotion_candidates
- test_auto_categorize

# View tests
- test_team_page_displays_categories
- test_manual_members_show_first
- test_points_members_ordered_correctly

# Assignment tests
- test_manual_assignment_overrides_points
- test_points_based_assignment
- test_promotion_candidate_flagging
```

---

## 🔄 Integration Points

### **With Existing Systems**

| System | Integration Point | Purpose |
|--------|------------------|---------|
| **Management App** | TaskHistory.point | Point calculation |
| **Management App** | Requirement.duration | Point calculation |
| **Management App** | Training.level | Point calculation |
| **Professional Services** | ClientAssessment | Point calculation |
| **Accounts App** | UserProfile | Display data |
| **Finance App** | Performance tier | Future integration |

---

## 📊 Scalability Architecture

### **Current Scale**
- 14 active team members
- 9 categories
- ~10 queries per page

### **Design Capacity**
- 1,000+ team members
- 20+ categories
- < 20 queries per page
- Sub-2 second load times

### **Scaling Strategy**
```python
# Horizontal scaling
- Read replicas for queries
- Page caching for high traffic
- CDN for static assets

# Vertical optimization
- Database indexes
- Query optimization (select_related)
- Points cached daily
```

---

## 🎨 UI/UX Architecture

### **Team Display Hierarchy**

```
Team Profiles Page
├── BOG/Leadership (priority-ordered)
│   ├── Amanda Towe (priority: 100)
│   ├── Chris Maghas (priority: 90)
│   └── Tirimba Obonyo (priority: 80)
├── Elite Team
│   └── Chris Maghas - coda-info (priority: 100)
├── Lead Team (priority-ordered)
│   ├── Edwin Kimtai (priority: 100)
│   ├── Emanuel Masakhwe (priority: 90)
│   └── George Ndahiro (priority: 80)
├── Support Team
├── Senior Analysts
└── Junior Analysts

Future Talents Page
├── Senior Trainee (points-ordered DESC)
│   ├── Bonie Luke (5,500 points)
│   └── Brenda Nasimiyu (5,200 points)
├── Junior Trainee (points-ordered DESC)
│   ├── Angel (4,800 points)
│   └── Eugene (4,300 points)
└── Elementary (points-ordered DESC)
    └── (New trainees < 4,000 points)
```

---

## 🔄 Data Synchronization

### **Point Recalculation**

```python
# Daily cron job at 2 AM
0 2 * * * cd /app && python manage.py recalculate_team_points

# Process:
1. Query non-manual members
2. Calculate points from 5 sources
3. Update TeamProfile.total_points
4. Check for promotion candidates
5. Auto-assign to appropriate group
```

### **Group Assignment**

```python
# Manual assignment (on-demand)
python manage.py assign_manual_team_members

# Auto assignment (daily with point recalculation)
python manage.py recalculate_team_points
```

---

## 📝 Design Decisions

### **Decision 1: Groups vs Fields**
**Chosen:** Django Groups + TeamProfile  
**Rationale:** Clean architecture, no UserProfile bloat  
**Trade-off:** Slightly more complex queries (acceptable)

### **Decision 2: TeamProfile Size**
**Chosen:** 5 fields only  
**Rationale:** Keep it small and focused  
**Trade-off:** None

### **Decision 3: Manual vs Points**
**Chosen:** Hybrid (manual for senior, points for trainees)  
**Rationale:** Best of both worlds  
**Trade-off:** Two logic paths (manageable)

### **Decision 4: Promotion Threshold**
**Chosen:** 6,000 points triggers manual review  
**Rationale:** Balance automation with quality control  
**Trade-off:** Admin must review candidates (acceptable)

---

**Continue to [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md)**

