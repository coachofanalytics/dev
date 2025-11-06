from django.contrib.auth import get_user_model
from management.models import Task, TaskHistory

User = get_user_model()

print("\n" + "="*70)
print("CHECKING USER: gndahiro")
print("="*70)

user = User.objects.filter(username='gndahiro').first()

if user:
    print(f"\n✓ User found!")
    print(f"  Email: {user.email}")
    print(f"  is_staff: {user.is_staff}")
    print(f"  is_active: {user.is_active}")
    
    tasks = Task.objects.filter(employee=user)
    print(f"\n📋 Current Tasks: {tasks.count()}")
    if tasks.count() > 0:
        for task in tasks[:3]:
            print(f"  - {task.activity_name}: {task.point} points")
    
    history = TaskHistory.objects.filter(employee=user)
    print(f"\n📚 TaskHistory Records: {history.count()}")
    
    if history.count() == 0:
        print("\n⚠️  NO TASKHISTORY - This is the bug! Tasks should have been moved.")
        print("   This confirms the issue you reported.")
    else:
        print(f"\n✓ User has {history.count()} TaskHistory records")
        
else:
    print("\n❌ User 'gndahiro' NOT FOUND in database")
    print("   Please check if username is correct")

print("\n" + "="*70)

