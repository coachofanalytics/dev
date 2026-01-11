# Manual Test Checklist - Career Ladder Implementation (26.01)

**Branch:** 26.01_CODA_DEV_CM  
**Date:** 2026-01-01  
**Status:** Pre-deployment verification

---

## Prerequisites

- Working on branch `26.01_CODA_DEV_CM`
- Local database is cloned production (safe for testing)
- All migrations have been created but NOT yet run

---

## Phase 1: Pre-Migration Verification

### 1.1 System Check
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py check
```
**Expected:** System check identified no issues (0 silenced)

### 1.2 Phase 0 Audit Script
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py shell -c "$(cat ../scripts/phase0_daf_audit.py)"
```
**Expected:** 
- Model field lists printed
- Counts and distributions shown
- No errors

---

## Phase 2: Migration Execution

### 2.1 Run Migrations
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py migrate accounts
```
**Expected:**
- Migration `0002_add_career_ladder_fields` applies successfully
- Migration `0003_populate_career_ladder_data` applies successfully
- No errors

### 2.2 Verify Migration Results (Django Shell)
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py shell
```

Then run:
```python
from accounts.models import TaskGroups, UserProfile
from accounts.models import CustomerUser

# Verify Group H/I marked as SPECIAL
group_h = TaskGroups.objects.filter(title='Group H').first()
group_i = TaskGroups.objects.filter(title='Group I').first()
print(f"Group H: track={group_h.track}, is_special={group_h.is_special}, code={group_h.code}")
print(f"Group I: track={group_i.track}, is_special={group_i.is_special}, code={group_i.code}")

# Verify default Growth Tier 1 exists
growth_t1 = TaskGroups.objects.filter(code='GROWTH_T1').first()
print(f"Growth Tier 1: {growth_t1.title if growth_t1 else 'NOT FOUND'}")

# Verify staff profiles have career_group set
staff_users = CustomerUser.objects.filter(is_staff=True, is_active=True)
profiles_without_group = UserProfile.objects.filter(user__in=staff_users, career_group__isnull=True).count()
print(f"Staff profiles without career_group: {profiles_without_group} (should be 0)")

# Sample check: verify a few staff users
for user in staff_users[:5]:
    if hasattr(user, 'profile'):
        print(f"{user.username}: career_group={user.profile.career_group.title if user.profile.career_group else 'None'}")
```

**Expected:**
- Group H: track=SPECIAL, is_special=True, code=SPECIAL_GROUP_H
- Group I: track=SPECIAL, is_special=True, code=SPECIAL_GROUP_I
- Growth Tier 1 exists
- Staff profiles without career_group: 0
- Sample users show career_group (likely "Growth Tier 1")

---

## Phase 3: Career Ladder Service & Command

### 3.1 Diagnose Career Ladder Command
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py diagnose_career_ladder
```
**Expected:**
- Monthly points distribution printed
- Curated cohort analysis shown
- Time-to-threshold analysis displayed
- Recommendations printed (advisory only)

### 3.2 Test Individual User
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py diagnose_career_ladder --username eunice
```
**Expected:**
- User analysis printed
- Total points shown
- Current track and tier displayed

---

## Phase 4: UI Verification

### 4.1 DAF v2 Page
**URL:** `http://127.0.0.1:8000/management/daf/v2/`

**Steps:**
1. Navigate to DAF v2 page
2. Check header area (near "My DAF" or employee name)
3. Look for career ladder badge (e.g., "GROWTH Tier 1")

**Expected:**
- Page loads without errors
- Badge appears next to employee name/header
- Badge shows format: `<TRACK> Tier <N>` (e.g., "GROWTH Tier 1")
- Badge uses Bootstrap `bg-info` style

**Test Users:**
- Self-view: `/management/daf/v2/`
- Staff viewing other: `/management/daf/v2/?user_id=2908` (judy_matunda)
- Staff viewing other: `/management/daf/v2/?user_id=495` (another user)

### 4.2 Task List Page
**URL:** `http://127.0.0.1:8000/management/tasks/`

**Steps:**
1. Navigate to task list page
2. Check "Employee" column in table
3. Look for career ladder badge next to employee names

**Expected:**
- Page loads without errors
- Badge appears in Employee column
- Badge shows for each employee row
- No template errors

### 4.3 Performance Report Page (if accessible)
**URL:** `http://127.0.0.1:8000/management/reports/performance/` (or similar)

**Steps:**
1. Navigate to performance report (staff only)
2. Check "Employee" column
3. Look for career ladder badge

**Expected:**
- Page loads without errors
- Badge appears next to employee usernames
- No template errors

### 4.4 Verify Policy Group Badge Still Works
**Check:** Existing "policy group" badges (Group A/B/C) should still render unchanged.

**Expected:**
- Policy group badges remain visible
- No conflicts with career ladder badge
- Both badges can appear simultaneously if needed

---

## Phase 5: Database Sanity Checks

### 5.1 Verify TaskGroups Integrity
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py shell
```

```python
from accounts.models import TaskGroups

# Verify existing Group A..I still exist with same IDs
all_groups = TaskGroups.objects.all().order_by('id')
for tg in all_groups:
    print(f"ID {tg.id}: {tg.title} | track={tg.track} | tier={tg.tier} | is_special={tg.is_special} | code={tg.code}")

# Verify no duplicate codes
from django.db.models import Count
duplicate_codes = TaskGroups.objects.values('code').annotate(count=Count('id')).filter(count__gt=1, code__isnull=False)
print(f"Duplicate codes: {list(duplicate_codes)}")
```

**Expected:**
- All Group A..I rows exist with same IDs as before
- Group H and Group I have track=SPECIAL, is_special=True
- No duplicate codes (except None values)

### 5.2 Verify UserProfile career_group
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py shell
```

```python
from accounts.models import UserProfile, CustomerUser

# Check staff profiles
staff_count = CustomerUser.objects.filter(is_staff=True, is_active=True).count()
profiles_with_group = UserProfile.objects.filter(user__is_staff=True, user__is_active=True, career_group__isnull=False).count()
profiles_without_group = UserProfile.objects.filter(user__is_staff=True, user__is_active=True, career_group__isnull=True).count()

print(f"Total active staff: {staff_count}")
print(f"Profiles with career_group: {profiles_with_group}")
print(f"Profiles without career_group: {profiles_without_group}")

# Sample a few profiles
sample_profiles = UserProfile.objects.filter(user__is_staff=True, user__is_active=True).select_related('career_group')[:5]
for profile in sample_profiles:
    cg = profile.career_group
    print(f"{profile.user.username}: {cg.title if cg else 'None'} ({cg.track if cg else 'N/A'} Tier {cg.tier if cg else 'N/A'})")
```

**Expected:**
- All staff profiles have career_group set (profiles_without_group = 0)
- Sample profiles show career_group (likely "Growth Tier 1" for default)

---

## Phase 6: Sample User Verification

### 6.1 Test Specific Users
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py shell
```

```python
from accounts.models import CustomerUser
from management.services.career_ladder_service import CareerLadderService

service = CareerLadderService()
test_users = ['eunice', 'makied', 'KEN', 'idah_w']

for username in test_users:
    try:
        user = CustomerUser.objects.get(username=username)
        if user.is_staff:
            total_points = service.compute_employee_points(user)
            track, tier = service.resolve_track_and_tier(float(total_points))
            cg = user.profile.career_group if hasattr(user, 'profile') else None
            print(f"{username}:")
            print(f"  Total points: {total_points}")
            print(f"  Resolved: {track} Tier {tier}")
            print(f"  Profile career_group: {cg.title if cg else 'None'}")
            print()
    except CustomerUser.DoesNotExist:
        print(f"{username}: User not found")
```

**Expected:**
- Users found and analyzed
- Points calculated correctly
- Track/tier resolved
- Profile career_group matches or can be updated

---

## Phase 7: Edge Cases & Error Handling

### 7.1 Missing Profile
**Test:** User without profile should not break template

**Expected:** Badge does not render (graceful failure)

### 7.2 Missing career_group
**Test:** Profile without career_group should not break template

**Expected:** Badge does not render (graceful failure)

### 7.3 Missing track/tier
**Test:** career_group without track/tier should fallback to title

**Expected:** Badge shows title instead of "Track Tier N"

---

## Phase 8: Performance Check

### 8.1 N+1 Query Check
**Verify:** Views use select_related to avoid N+1 queries

**Check:**
- `daf_v2_view`: Uses `select_related('employee__profile', 'employee__profile__career_group')`
- `TaskListView`: Uses `select_related('employee__profile', 'employee__profile__career_group')`
- `performance_report`: Uses `select_related('profile', 'profile__career_group')`

---

## Summary Checklist

- [ ] System check passes
- [ ] Phase 0 audit script runs successfully
- [ ] Migrations apply cleanly
- [ ] Group H/I marked as SPECIAL
- [ ] Default Growth Tier 1 created
- [ ] All staff profiles have career_group set
- [ ] diagnose_career_ladder command runs
- [ ] DAF v2 page shows badge
- [ ] Task list page shows badge
- [ ] Performance report shows badge (if accessible)
- [ ] Policy group badges still work
- [ ] No template errors
- [ ] Sample users (eunice, makied, KEN, idah_w) show correct badges
- [ ] No N+1 query issues

---

## Known Issues / Notes

- **DO NOT PUSH TO GITHUB** - This is local verification only
- Career ladder is separate from policy groups (Group A/B/C)
- Legacy `employee_group_level` function remains intact
- Group H/I are excluded from ladder progression

---

## Next Steps (After Verification)

1. If all checks pass: Ready for UAT branch merge
2. If issues found: Document and fix before proceeding
3. **DO NOT DEPLOY TO PRODUCTION** until explicit approval

---

---

## Phase 9: Career Ladder Progression (New)

### 9.1 Dry-Run Progression Command
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py apply_career_ladder_progression --dry-run
```

**Expected:**
- Shows what would be changed without making changes
- Lists users with current group and target group
- Shows total points and resolved track/tier
- No actual database changes

### 9.2 Test Specific User
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py apply_career_ladder_progression --dry-run --user eunice
```

**Expected:**
- Shows progression for specific user only
- Displays current vs target career_group
- Shows total lifetime points

### 9.3 Apply Progression (After Dry-Run Verification)
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py apply_career_ladder_progression
```

**Expected:**
- Updates UserProfile.career_group for users whose computed tier differs
- Logs changes clearly
- Idempotent: running again should show "No changes needed" for same users

### 9.4 Verify Profile Updates
```bash
cd /Users/coda/Projects/uat/coda
poetry run python manage.py shell
```

```python
from accounts.models import UserProfile, CustomerUser
from django.db.models import Count

# Check distribution after progression
distribution = UserProfile.objects.filter(
    user__is_staff=True,
    user__is_active=True
).values(
    "career_group__title",
    "career_group__track",
    "career_group__tier"
).annotate(n=Count("id")).order_by("-n")

print("Career group distribution after progression:")
for item in distribution:
    print(f"  {item['career_group__title']} / {item['career_group__track']} / tier {item['career_group__tier']} (n={item['n']})")
```

**Expected:**
- Distribution shows updated career groups
- Users with higher points show higher tiers
- SPECIAL groups (H/I) remain unchanged

### 9.5 UI Verification After Progression
**Steps:**
1. Run progression command
2. Load DAF v2 page: `http://127.0.0.1:8000/management/daf/v2/`
3. Load Task list page: `http://127.0.0.1:8000/management/tasks/`
4. Check performance report (if accessible)

**Expected:**
- Badge reflects updated career_group after progression
- Badge shows correct track and tier
- No template errors

### 9.6 DAF Reset Integration (Optional)
**Note:** Career ladder progression is hooked into DAF reset but disabled by default.

To enable:
```python
# In settings.py or local_settings.py
CAREER_LADDER_AUTO_APPLY_ON_RESET = True
```

**Expected:**
- Progression runs automatically after monthly task reset
- Logs show progression applied
- No errors in reset process

---

**Last Updated:** 2026-01-01  
**Verified By:** [Your Name]

