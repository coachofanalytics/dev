# ARCHITECTURE DESIGN

**Document:** 3 of 7  
**Created:** November 5, 2025  
**Purpose:** System architecture and design decisions

---

## 🏗️ SYSTEM ARCHITECTURE

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│  Browser (Desktop/Mobile) → Django Templates          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                   │
│  Views → Templates → Static Assets                      │
│  - team() view                                          │
│  - about() view                                         │
│  - team_profiles.html                                   │
│  - team_card.html                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                 │
│  Services → Managers → Utilities                        │
│  - TeamService (point calculation)                      │
│  - TeamAssignmentService (assignments)                  │
│  - DescriptionService (AI generation)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                    │
│  Models → Querysets → Cache                            │
│  - UserProfile                                         │
│  - TeamAssignment (new)                                │
│  - Assets                                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    DATA STORAGE LAYER                   │
│  PostgreSQL → Redis → Google Drive                     │
│  - Team data in PostgreSQL                             │
│  - Points cache in Redis (optional)                     │
│  - Images in Google Drive                              │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 DATA MODEL DESIGN

### **Option A: Extended UserProfile**

```python
class UserProfile(models.Model):
    # Existing fields...
    user = OneToOneField(CustomerUser)
    position = CharField()
    description = TextField()
    
    # New fields for team assignment
    team_category = CharField(
        max_length=50,
        choices=TEAM_CATEGORIES,
        null=True,
        blank=True,
        db_index=True
    )
    team_priority = IntegerField(default=0, db_index=True)
    is_manually_assigned = BooleanField(default=False)
    total_points = IntegerField(default=0, db_index=True)
    total_points_calculated_at = DateTimeField(null=True)
```

**Pros:**
- Simple
- Single query
- Fast

**Cons:**
- Less normalized
- No audit trail

---

### **Option B: Separate TeamAssignment Model** ⭐ **RECOMMENDED**

```python
class TeamAssignment(models.Model):
    CATEGORY_CHOICES = [
        ('bog_leadership', 'BOG/Leadership'),
        ('elite', 'Elite Team'),
        ('lead', 'Lead Team'),
        ('support', 'Support Team'),
        ('senior_analyst', 'Senior Analysts'),
        ('junior_analyst', 'Junior Analysts'),
        ('senior_trainee', 'Senior Trainee'),
        ('junior_trainee', 'Junior Trainee'),
    ]
    
    user_profile = ForeignKey(UserProfile, on_delete=CASCADE)
    category = CharField(max_length=50, choices=CATEGORY_CHOICES)
    is_manual = BooleanField(default=False)
    priority = IntegerField(default=0, db_index=True)
    display_order = IntegerField(default=0)
    assigned_by = ForeignKey(User, null=True)
    assigned_at = DateTimeField(auto_now_add=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        unique_together = [['user_profile', 'category', 'is_active']]
        indexes = [
            Index(fields=['category', 'priority']),
            Index(fields=['is_active', 'category']),
        ]
        ordering = ['priority', 'display_order', '-assigned_at']
```

**Pros:**
- Normalized
- Audit trail
- Flexible
- Historical tracking

---

## 🔧 SERVICE LAYER DESIGN

### **TeamService**

```python
# services/team_service.py

class TeamService:
    @staticmethod
    def calculate_total_points(user_profile):
        """Calculate total points from all sources"""
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
    def get_team_category(user_profile):
        """Get team category (manual override or points-based)"""
        # Check manual assignment first
        manual_assignment = TeamAssignment.objects.filter(
            user_profile=user_profile,
            is_active=True,
            is_manual=True
        ).first()
        
        if manual_assignment:
            return manual_assignment.category
        
        # Fall back to points-based
        points = user_profile.total_points
        return TeamService._category_from_points(points)
    
    @staticmethod
    def get_team_members_by_category(category):
        """Get all team members in a category"""
        # Get manual assignments
        manual = TeamAssignment.objects.filter(
            category=category,
            is_active=True,
            is_manual=True
        ).select_related('user_profile').order_by('priority', 'display_order')
        
        # Get points-based assignments (if not manually assigned)
        manual_user_ids = [a.user_profile_id for a in manual]
        points_based = UserProfile.objects.filter(
            user__category=2,
            user__is_active=True
        ).exclude(
            id__in=manual_user_ids
        ).annotate(
            category_from_points=Case(
                When(total_points__gte=8000, then=Value('lead')),
                When(total_points__gte=7000, then=Value('senior_analyst')),
                # ... etc
            )
        ).filter(
            category_from_points=category
        ).order_by('-total_points')
        
        # Combine and sort
        all_members = list(manual) + list(points_based)
        return sorted(all_members, key=lambda x: (
            x.priority if hasattr(x, 'priority') else 0,
            -x.user_profile.total_points if hasattr(x, 'user_profile') else 0
        ))
```

---

## 🎨 PRESENTATION LAYER DESIGN

### **View Structure**

```python
# views.py

def team(request, title):
    """Main team view - handles all team pages"""
    # Get team categories based on page type
    if title == 'team_profiles':
        categories = [
            'bog_leadership',
            'elite',
            'lead',
            'support',
            'senior_analyst',
        ]
    elif title == 'future_talents':
        categories = [
            'junior_analyst',
            'senior_trainee',
            'junior_trainee',
        ]
    elif title == 'board':
        categories = ['bog_leadership']
    else:
        categories = []
    
    # Get team members for each category
    team_categories = {}
    for category in categories:
        members = TeamService.get_team_members_by_category(category)
        if members:
            team_categories[category] = members
    
    context = {
        'team_categories': team_categories,
        'title': get_heading_for_page(title),
    }
    
    return render(request, 'main/team_profiles.html', context)
```

---

## 🔄 CACHING STRATEGY

### **Multi-Level Caching**

```
1. Page-Level Cache (1 hour)
   ↓
2. Query Result Cache (30 minutes)
   ↓
3. Calculated Points Cache (24 hours)
   ↓
4. Database Field (permanent until recalculation)
```

### **Implementation**

```python
# Cache calculated points
@cache_page(60 * 60)  # 1 hour
def team(request, title):
    # Use cached points from database
    members = UserProfile.objects.filter(
        user__category=2
    ).select_related('user').prefetch_related('teamassignment_set')
    
    # Points already cached in total_points field
    # No calculation needed
```

---

## 🔐 SECURITY DESIGN

### **Access Control**

```python
# Permissions
- View team pages: PUBLIC
- View total points: ADMIN/STAFF only
- Edit team assignments: ADMIN only
- Edit profile: OWNER or ADMIN

# Data Protection
- XSS: Remove |safe filters, use auto-escape
- CSRF: Django middleware
- Rate Limiting: AI generation
- Image Validation: File type, size checks
```

---

## 📈 PERFORMANCE OPTIMIZATION

### **Query Optimization**

```python
# Use select_related and prefetch_related
members = UserProfile.objects.filter(
    user__category=2
).select_related(
    'user',
    'image2'
).prefetch_related(
    'teamassignment_set'
).annotate(
    total_points=F('total_points')  # Use cached field
).order_by('team_priority', '-total_points')

# Result: 1-2 queries instead of 100+
```

### **Database Indexes**

```python
# Add indexes for common queries
class Meta:
    indexes = [
        Index(fields=['team_category', 'team_priority']),
        Index(fields=['total_points']),
        Index(fields=['is_manually_assigned', 'team_category']),
    ]
```

---

## 🧪 TESTING ARCHITECTURE

### **Test Structure**

```
tests/
├── test_models.py          # Model tests
├── test_services.py        # Service layer tests
├── test_views.py          # View tests
├── test_team_assignment.py # Team assignment tests
└── test_point_calculation.py # Point calculation tests
```

---

## 📝 NEXT STEPS

1. **Review architecture** - Confirm design decisions
2. **Review Document 4** - Select improvement options
3. **Review Document 6** - Implementation details

---

**Continue to Document 6: [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)**

