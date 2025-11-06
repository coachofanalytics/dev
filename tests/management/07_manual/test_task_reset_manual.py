"""
Manual test script for task reset bug fix
Run this with: python manage.py shell < test_task_reset_manual.py
"""

from django.contrib.auth import get_user_model
from management.models import Task, TaskHistory, TaskCategory
from accounts.models import TaskGroups
from coda_project.task import dump_data
from decimal import Decimal
from unittest.mock import Mock

User = get_user_model()

print("\n" + "="*70)
print("TESTING TASK RESET BUG FIX")
print("="*70)

# Test 1: Employee with NO prior TaskHistory (the bug case)
print("\n📋 TEST 1: Employee with NO TaskHistory (Bug Fix Test)")
print("-" * 70)

# Check if test user already exists
test_user = User.objects.filter(username='test_newemployee_fix').first()
if test_user:
    # Clean up old test data
    print("Cleaning up existing test data...")
    TaskHistory.objects.filter(employee=test_user).delete()
    Task.objects.filter(employee=test_user).delete()
    test_user.delete()

# Create new test employee
employee = User.objects.create_user(
    username='test_newemployee_fix',
    email='testnew@test.com',
    is_staff=True,
    is_active=True
)
print(f"✓ Created test employee: {employee.username}")

# Get or create group and category
group, _ = TaskGroups.objects.get_or_create(
    name='Test Group Fix',
    defaults={'description': 'Test group for bug fix'}
)
category, _ = TaskCategory.objects.get_or_create(
    title='Other',
    defaults={'description': 'Test category'}
)

# Create test tasks
task1 = Task.objects.create(
    employee=employee,
    groupname=group,
    category=category,
    activity_name='Test Task 1',
    description='Test description',
    point=Decimal('50.00'),
    mxpoint=Decimal('100.00'),
    mxearning=Decimal('100.00'),
    group='Group A'
)
task2 = Task.objects.create(
    employee=employee,
    groupname=group,
    category=category,
    activity_name='Test Task 2',
    description='Test description',
    point=Decimal('30.00'),
    mxpoint=Decimal('100.00'),
    mxearning=Decimal('100.00'),
    group='Group A'
)
print(f"✓ Created 2 test tasks with points: {task1.point}, {task2.point}")

# Check TaskHistory BEFORE reset
history_before = TaskHistory.objects.filter(employee=employee).count()
print(f"\n📊 TaskHistory count BEFORE reset: {history_before}")

if history_before > 0:
    print("⚠️  WARNING: Employee already has TaskHistory (not a pure test)")
else:
    print("✓ Confirmed: NO TaskHistory exists (pure bug test case)")

# Run the dump_data function (task reset)
print("\n🔄 Running dump_data (task reset)...")
request = Mock()
try:
    result = dump_data(request)
    print(f"✓ dump_data completed: {result}")
except Exception as e:
    print(f"❌ ERROR running dump_data: {e}")
    result = False

# Check TaskHistory AFTER reset
history_after = TaskHistory.objects.filter(employee=employee).count()
print(f"\n📊 TaskHistory count AFTER reset: {history_after}")

# Check task points after reset
task1.refresh_from_db()
task2.refresh_from_db()
print(f"📊 Task points after reset: Task1={task1.point}, Task2={task2.point}")

# Evaluate results
print("\n" + "="*70)
print("TEST RESULTS:")
print("="*70)

if history_after == 2 and task1.point == 0 and task2.point == 0:
    print("✅ TEST PASSED!")
    print("   - Tasks moved to TaskHistory: YES")
    print("   - TaskHistory count: 2 (correct)")
    print("   - Task points reset to 0: YES")
    print("\n🎉 BUG FIX VERIFIED: Tasks now move to history for new employees!")
else:
    print("❌ TEST FAILED!")
    if history_after != 2:
        print(f"   - Expected 2 TaskHistory records, got {history_after}")
    if task1.point != 0:
        print(f"   - Task1 points not reset (expected 0, got {task1.point})")
    if task2.point != 0:
        print(f"   - Task2 points not reset (expected 0, got {task2.point})")
    print("\n⚠️  BUG STILL EXISTS or different issue!")

# Cleanup
print("\n🧹 Cleaning up test data...")
TaskHistory.objects.filter(employee=employee).delete()
Task.objects.filter(employee=employee).delete()
employee.delete()
print("✓ Cleanup complete")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)

