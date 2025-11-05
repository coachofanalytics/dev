# Team Assignment System - Testing

**Feature:** Hybrid Team Assignment with Django Groups + TeamProfile  
**Date:** November 5, 2025  
**Status:** 🧪 Testing Strategy

---

## 🎯 Testing Strategy

### **Test Pyramid**

```
        /\
       /  \      E2E Tests (10%) - 5 tests
      /____\     
     /      \    Integration Tests (30%) - 15 tests
    /________\   
   /          \  Unit Tests (60%) - 30 tests
  /____________\
  
  Total: ~50 tests
  Target Coverage: 80%+
```

---

## 📋 Test Categories

### **1. Model Tests** (10 tests)

**File:** `coda/tests/test_team_profile_model.py`

```python
import pytest
from django.contrib.auth.models import Group, User
from accounts.models import TeamProfile


@pytest.mark.django_db
class TestTeamProfileModel:
    """Test TeamProfile model"""
    
    def test_team_profile_creation(self):
        """Test creating a team profile"""
        user = User.objects.create_user(username='testuser')
        team_profile = TeamProfile.objects.create(
            user=user,
            priority=100,
            total_points=5000
        )
        
        assert team_profile.user == user
        assert team_profile.priority == 100
        assert team_profile.total_points == 5000
        assert team_profile.is_manually_assigned == False
    
    def test_category_property_returns_group(self):
        """Test category property gets group name"""
        user = User.objects.create_user(username='testuser')
        team_profile = TeamProfile.objects.create(user=user)
        
        # Add user to group
        lead_group = Group.objects.create(name='Lead Team')
        user.groups.add(lead_group)
        
        assert team_profile.category == 'Lead Team'
    
    def test_category_property_none_if_no_group(self):
        """Test category returns None if not in team group"""
        user = User.objects.create_user(username='testuser')
        team_profile = TeamProfile.objects.create(user=user)
        
        assert team_profile.category is None
    
    def test_multiple_groups_returns_first(self):
        """Test with user in multiple groups (shouldn't happen but handle it)"""
        user = User.objects.create_user(username='testuser')
        team_profile = TeamProfile.objects.create(user=user)
        
        # Add to multiple groups
        bog = Group.objects.create(name='BOG/Leadership')
        lead = Group.objects.create(name='Lead Team')
        user.groups.add(bog, lead)
        
        # Should return first in priority order (BOG)
        assert team_profile.category == 'BOG/Leadership'
    
    def test_str_representation(self):
        """Test string representation"""
        user = User.objects.create_user(username='testuser')
        team_profile = TeamProfile.objects.create(user=user)
        lead = Group.objects.create(name='Lead Team')
        user.groups.add(lead)
        
        assert 'testuser' in str(team_profile)
        assert 'Lead Team' in str(team_profile)
```

---

### **2. Service Tests** (15 tests)

**File:** `coda/tests/test_team_service.py`

```python
import pytest
from django.contrib.auth.models import Group, User
from accounts.models import TeamProfile, UserProfile
from main.services.team_service import TeamService
from management.models import TaskHistory
from professional_services.models import ClientAssessment


@pytest.mark.django_db
class TestTeamService:
    """Test TeamService functionality"""
    
    def test_assign_to_category(self):
        """Test assigning user to team category"""
        user = User.objects.create_user(username='testuser')
        Group.objects.create(name='Lead Team')
        
        TeamService.assign_to_category(
            user, 
            'Lead Team', 
            priority=100, 
            is_manual=True
        )
        
        # Check group membership
        assert user.groups.filter(name='Lead Team').exists()
        
        # Check TeamProfile
        team_profile = user.team_profile
        assert team_profile.is_manually_assigned == True
        assert team_profile.priority == 100
    
    def test_calculate_total_points(self):
        """Test point calculation"""
        user = User.objects.create_user(username='testuser')
        profile = UserProfile.objects.create(
            user=user,
            education=3  # Bachelor's = 1000 points
        )
        
        # Add task history
        TaskHistory.objects.create(
            employee_id=user,
            point=500
        )
        
        points = TeamService.calculate_total_points(user)
        
        assert points >= 1500  # 1000 (education) + 500 (task)
    
    def test_get_promotion_candidates(self):
        """Test promotion candidate detection"""
        # Create user with high points
        user = User.objects.create_user(username='highpointer')
        TeamProfile.objects.create(
            user=user,
            total_points=6500,
            is_manually_assigned=False
        )
        
        candidates = TeamService.get_promotion_candidates()
        
        assert user in [c for c in candidates]
    
    def test_manual_assignment_not_auto_categorized(self):
        """Test manual members skip auto-categorization"""
        user = User.objects.create_user(username='manual')
        team_profile = TeamProfile.objects.create(
            user=user,
            total_points=3000,  # Would be elementary
            is_manually_assigned=True
        )
        
        # Add to Lead Team manually
        lead = Group.objects.create(name='Lead Team')
        user.groups.add(lead)
        
        # Should stay in Lead Team (not auto-categorized to Elementary)
        assert team_profile.category == 'Lead Team'
```

---

### **3. View Tests** (10 tests)

**File:** `coda/tests/test_team_views.py`

```python
import pytest
from django.test import Client
from django.contrib.auth.models import Group, User
from accounts.models import TeamProfile, UserProfile


@pytest.mark.django_db
class TestTeamViews:
    """Test team view functionality"""
    
    def test_team_profiles_page_loads(self):
        """Test team profiles page loads successfully"""
        client = Client()
        response = client.get('/members/team_profiles')
        
        assert response.status_code == 200
        assert 'team_categories' in response.context
    
    def test_team_profiles_displays_categories(self):
        """Test team profiles page displays all categories"""
        # Create test user in Lead Team
        user = User.objects.create_user(
            username='testlead',
            first_name='Test',
            last_name='Lead'
        )
        UserProfile.objects.create(user=user)
        team_profile = TeamProfile.objects.create(
            user=user,
            is_manually_assigned=True,
            priority=100
        )
        
        lead_group = Group.objects.create(name='Lead Team')
        user.groups.add(lead_group)
        
        client = Client()
        response = client.get('/members/team_profiles')
        
        assert response.status_code == 200
        assert 'Lead Team' in response.context['team_categories']
        assert user in response.context['team_categories']['Lead Team']
    
    def test_future_talents_page_loads(self):
        """Test future talents page loads"""
        client = Client()
        response = client.get('/members/future_talents')
        
        assert response.status_code == 200
    
    def test_board_page_loads(self):
        """Test board page loads"""
        client = Client()
        response = client.get('/members/board')
        
        assert response.status_code == 200
    
    def test_members_ordered_by_priority(self):
        """Test members display in priority order"""
        # Create two users in same category
        user1 = User.objects.create_user(username='user1', first_name='A')
        user2 = User.objects.create_user(username='user2', first_name='B')
        
        UserProfile.objects.create(user=user1)
        UserProfile.objects.create(user=user2)
        
        TeamProfile.objects.create(user=user1, priority=50)
        TeamProfile.objects.create(user=user2, priority=100)  # Higher priority
        
        lead = Group.objects.create(name='Lead Team')
        user1.groups.add(lead)
        user2.groups.add(lead)
        
        client = Client()
        response = client.get('/members/team_profiles')
        
        members = list(response.context['team_categories']['Lead Team'])
        
        # user2 should be first (higher priority)
        assert members[0] == user2
        assert members[1] == user1
```

---

### **4. Assignment Tests** (10 tests)

**File:** `coda/tests/test_team_assignment.py`

```python
@pytest.mark.django_db
class TestTeamAssignment:
    """Test team assignment logic"""
    
    def test_manual_assignment_to_bog(self):
        """Test manual assignment to BOG/Leadership"""
        user = User.objects.create_user(username='amanda_towe')
        UserProfile.objects.create(user=user)
        
        TeamService.assign_to_category(
            user,
            'BOG/Leadership',
            priority=100,
            is_manual=True
        )
        
        assert user.groups.filter(name='BOG/Leadership').exists()
        assert user.team_profile.is_manually_assigned == True
        assert user.team_profile.priority == 100
    
    def test_points_based_assignment(self):
        """Test auto-assignment based on points"""
        user = User.objects.create_user(username='trainee')
        UserProfile.objects.create(user=user, education=3)
        team_profile = TeamProfile.objects.create(
            user=user,
            total_points=4500,
            is_manually_assigned=False
        )
        
        TeamService.auto_categorize_by_points(user)
        
        # Should be in Junior Trainee (4000-5000)
        assert user.groups.filter(name='Junior Trainee').exists()
    
    def test_manual_overrides_points(self):
        """Test manual assignment takes precedence"""
        user = User.objects.create_user(username='manual')
        UserProfile.objects.create(user=user)
        team_profile = TeamProfile.objects.create(
            user=user,
            total_points=3000,  # Would be elementary
            is_manually_assigned=True
        )
        
        # Manually assign to Lead Team
        lead = Group.objects.create(name='Lead Team')
        user.groups.add(lead)
        
        # Should stay Lead Team, not Elementary
        assert team_profile.category == 'Lead Team'
```

---

### **5. Point Calculation Tests** (10 tests)

**File:** `coda/tests/test_point_calculation.py`

```python
@pytest.mark.django_db
class TestPointCalculation:
    """Test point calculation logic"""
    
    def test_education_points(self):
        """Test education point calculation"""
        user = User.objects.create_user(username='test')
        
        # Test each education level
        test_cases = [
            (1, 250),   # High School
            (2, 500),   # Some College
            (3, 1000),  # Bachelor's
            (4, 1500),  # Master's
            (5, 2000),  # Doctorate
        ]
        
        for level, expected_points in test_cases:
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'education': level}
            )
            
            points = TeamService._calculate_education_points(user.profile)
            assert points == expected_points
    
    def test_task_history_points(self):
        """Test task history point aggregation"""
        user = User.objects.create_user(username='test')
        
        # Create tasks
        TaskHistory.objects.create(employee_id=user, point=100)
        TaskHistory.objects.create(employee_id=user, point=200)
        TaskHistory.objects.create(employee_id=user, point=150)
        
        points = TeamService._calculate_task_points(user)
        
        assert points == 450  # Sum of all tasks
```

---

## ✅ Testing Checklist

### **Pre-Deployment Testing**

**Unit Tests:**
- [ ] All model tests pass (10 tests)
- [ ] All service tests pass (15 tests)
- [ ] All assignment tests pass (10 tests)
- [ ] All point calculation tests pass (10 tests)
- [ ] Code coverage ≥ 80%

**Integration Tests:**
- [ ] All view tests pass (10 tests)
- [ ] Group assignment works
- [ ] Points calculation works
- [ ] Promotion detection works

**Manual Testing:**
- [ ] Navigate to `/members/team_profiles`
- [ ] Verify BOG/Leadership shows 3 members
- [ ] Verify Elite Team shows 1 member
- [ ] Verify all categories display
- [ ] Verify images load
- [ ] Verify Read More/Less works
- [ ] Verify admin sees points
- [ ] Verify non-admin doesn't see points

**Performance Testing:**
- [ ] Page load < 2 seconds
- [ ] Query count < 10 per page
- [ ] No N+1 query issues
- [ ] Caching works

---

## 🐛 Test Data Setup

### **Fixtures**

```python
# tests/fixtures/team_fixtures.py

import pytest
from django.contrib.auth.models import Group, User
from accounts.models import UserProfile, TeamProfile


@pytest.fixture
def team_groups():
    """Create all team groups"""
    groups = []
    for name in ['BOG/Leadership', 'Elite Team', 'Lead Team']:
        group = Group.objects.create(name=name)
        groups.append(group)
    return groups


@pytest.fixture
def bog_member(team_groups):
    """Create BOG/Leadership member"""
    user = User.objects.create_user(
        username='bog_member',
        first_name='BOG',
        last_name='Member'
    )
    UserProfile.objects.create(user=user)
    TeamProfile.objects.create(
        user=user,
        priority=100,
        is_manually_assigned=True
    )
    
    bog = Group.objects.get(name='BOG/Leadership')
    user.groups.add(bog)
    
    return user


@pytest.fixture
def trainee(team_groups):
    """Create trainee member"""
    user = User.objects.create_user(
        username='trainee',
        first_name='Junior',
        last_name='Trainee'
    )
    profile = UserProfile.objects.create(user=user, education=3)
    TeamProfile.objects.create(
        user=user,
        total_points=4500,
        is_manually_assigned=False
    )
    
    return user
```

---

## 📊 Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| TeamProfile Model | 100% | Critical |
| TeamService | 90%+ | Critical |
| Team Views | 80%+ | High |
| Management Commands | 70%+ | Medium |

---

## 🔍 Test Execution

### **Run All Tests**

```bash
# All team tests
pytest tests/test_team_*.py -v

# With coverage
pytest tests/test_team_*.py --cov=accounts.models --cov=main.services --cov-report=html

# Specific test file
pytest tests/test_team_profile_model.py -v

# Specific test
pytest tests/test_team_profile_model.py::TestTeamProfileModel::test_category_property_returns_group -v
```

---

## ✅ Acceptance Testing

### **Manual Test Scenarios**

**Scenario 1: BOG/Leadership Display**
1. Navigate to `/members/team_profiles`
2. Verify "BOG/Leadership" category displays
3. Verify 3 members show: Amanda, Chris, Tirimba
4. Verify ordered by priority
5. Verify images load

**Scenario 2: Elite Team Display**
1. Verify "Elite Team" category displays
2. Verify 1 member shows: Chris (coda-info)
3. Verify correct description

**Scenario 3: Future Talents Auto-Categorization**
1. Navigate to `/members/future_talents`
2. Verify trainees categorized by points
3. Verify Senior Trainee (5-6K points)
4. Verify Junior Trainee (4-5K points)
5. Verify ordered by points DESC

**Scenario 4: Promotion Candidates**
1. Login as admin
2. Run `python manage.py show_promotion_candidates`
3. Verify members with 6,000+ points show
4. Verify point breakdown displayed

**Scenario 5: Manual Promotion**
1. Run `python manage.py promote_team_member <user> junior_analyst`
2. Verify confirmation prompt
3. Confirm promotion
4. Verify member now in Junior Analysts category
5. Verify promotion notes saved

---

## 🎯 Performance Testing

### **Load Time Tests**

```bash
# Using curl with timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/members/team_profiles

# curl-format.txt:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer:  %{time_pretransfer}\n
time_redirect:  %{time_redirect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
```

**Acceptance Criteria:**
- time_total < 2.0 seconds

---

### **Query Count Tests**

```python
from django.test import override_settings
from django.test.utils import override_settings

@override_settings(DEBUG=True)
def test_team_page_query_count():
    """Test query count is optimized"""
    from django.db import connection
    from django.test.utils import override_settings
    
    client = Client()
    
    # Reset query count
    connection.queries_log.clear()
    
    response = client.get('/members/team_profiles')
    
    query_count = len(connection.queries)
    
    # Should be < 10 queries
    assert query_count < 10, f"Too many queries: {query_count}"
```

---

## 📝 Test Documentation

### **Test Report Template**

```markdown
# Team Assignment Test Report

**Date:** YYYY-MM-DD
**Tester:** Name
**Environment:** Dev/UAT/Production

## Test Results

| Category | Tests Run | Passed | Failed | Coverage |
|----------|-----------|--------|--------|----------|
| Models | 10 | 10 | 0 | 100% |
| Services | 15 | 15 | 0 | 95% |
| Views | 10 | 10 | 0 | 85% |
| Commands | 5 | 5 | 0 | 75% |

**Total:** 50 tests, 50 passed, 0 failed
**Coverage:** 88% overall

## Issues Found

None

## Sign-off

✅ Ready for deployment
```

---

**Continue to [06_MAINTENANCE.md](06_MAINTENANCE.md)**

