from accounts.models import CustomerUser
from accounts.choices import UserCategory
from django.db.models import Count

print("\n" + "="*80)
print("CATEGORY REALITY CHECK: What's Actually in the Database?")
print("="*80)

# 1. Count users per category
print("\n📊 CATEGORY COUNTS:")
print("-"*80)
cat_counts = CustomerUser.objects.values('category').annotate(count=Count('id')).order_by('category')
for item in cat_counts:
    cat = item['category']
    count = item['count']
    print(f"Category {cat}: {count} users")

# 2. Show what choices.py says
print("\n📖 WHAT CHOICES.PY DEFINES:")
print("-"*80)
for value, label in UserCategory.choices:
    print(f"{value} = {label}")

# 3. Sample users per category
print("\n🔍 SAMPLE USERS PER CATEGORY (showing first 3):")
print("-"*80)
for cat_value in sorted([c['category'] for c in cat_counts]):
    samples = CustomerUser.objects.filter(category=cat_value)[:3]
    print(f"\n📂 Category {cat_value} ({samples.count()} total):")
    for user in samples:
        groups = ', '.join([g.name for g in user.groups.all()]) or 'None'
        print(f"  • {user.username:30} | {user.get_full_name():25} | is_staff={user.is_staff} | Groups: {groups}")

# 4. Check for Team Group assignments
print("\n🏢 TEAM GROUP ASSIGNMENTS:")
print("-"*80)
from django.contrib.auth.models import Group
team_groups = ['BOG-Leadership', 'Elite Team', 'Lead Team', 'Support Team', 'Senior Analysts', 'Junior Analysts', 'Senior Trainee', 'Junior Trainee', 'Elementary', 'Available for Hire']
for group_name in team_groups:
    try:
        group = Group.objects.get(name=group_name)
        count = group.user_set.filter(is_active=True).count()
        if count > 0:
            print(f"{group_name:25}: {count} members")
            for user in group.user_set.filter(is_active=True)[:3]:
                print(f"  • {user.username:30} | Category: {user.category} | is_staff: {user.is_staff}")
    except:
        pass

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)

