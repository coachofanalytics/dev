"""
Check which employees are PAID vs PRACTICING
Based on category and sub_category
"""

from django.contrib.auth import get_user_model
from accounts.choices import UserCategory, ApplicantSubCategoryChoices
from management.models import Task, TaskHistory
from management.services.employee_compliance_service import EmployeeComplianceService
from django.db.models import Sum
from decimal import Decimal

User = get_user_model()

print("\n" + "="*80)
print("EMPLOYEE PAYMENT STATUS ANALYSIS")
print("="*80)

# Get all active staff employees
all_employees = User.objects.filter(is_staff=True, is_active=True).order_by('username')

paid_employees = []
practicing_employees = []
compliance_service = EmployeeComplianceService()

# Get current month for compliance check
target_month, target_year = compliance_service.get_current_target_month_year()

print(f"\n📅 Checking compliance for: {target_month}/{target_year}")
print(f"📏 33% Rule Active: {'Yes' if compliance_service.is_compliance_rule_active() else 'No'}")

for employee in all_employees:
    # Check if FULL_TIME APPLICANT (paid employee)
    is_paid = (
        employee.category == UserCategory.APPLICANT and 
        employee.sub_category == ApplicantSubCategoryChoices.FULL_TIME
    )
    
    # Get task stats
    tasks = Task.objects.filter(employee=employee)
    task_count = tasks.count()
    total_points = tasks.aggregate(total=Sum('point'))['total'] or Decimal('0')
    
    # Get history
    history = TaskHistory.objects.filter(employee=employee)
    history_count = history.count()
    
    # Check 33% compliance
    compliance = compliance_service.check_33_percent_compliance(
        employee, target_month, target_year
    )
    
    emp_data = {
        'username': employee.username,
        'email': employee.email,
        'category': employee.get_category_display() if hasattr(employee, 'get_category_display') else employee.category,
        'sub_category': employee.get_sub_category_display() if hasattr(employee, 'get_sub_category_display') else employee.sub_category,
        'is_paid': is_paid,
        'tasks': task_count,
        'points': total_points,
        'history': history_count,
        'compliant': compliance['is_compliant'],
        'completion_rate': compliance['completion_rate']
    }
    
    if is_paid:
        paid_employees.append(emp_data)
    else:
        practicing_employees.append(emp_data)

print("\n" + "="*80)
print(f"💰 PAID EMPLOYEES (FULL-TIME APPLICANTS): {len(paid_employees)}")
print("="*80)

if paid_employees:
    for emp in paid_employees:
        status = "✅ Compliant" if emp['compliant'] else "❌ Non-compliant"
        print(f"\n{emp['username']}")
        print(f"  Category: {emp['category']} / {emp['sub_category']}")
        print(f"  Tasks: {emp['tasks']} | Points: {emp['points']}")
        print(f"  History: {emp['history']} records")
        print(f"  Compliance: {emp['completion_rate']:.1f}% {status}")
else:
    print("  No FULL-TIME paid employees found!")

print("\n" + "="*80)
print(f"📚 PRACTICING EMPLOYEES (Non-paid): {len(practicing_employees)}")
print("="*80)

if practicing_employees:
    for emp in practicing_employees:
        print(f"\n{emp['username']}")
        print(f"  Category: {emp['category']} / {emp['sub_category']}")
        print(f"  Tasks: {emp['tasks']} | Points: {emp['points']}")
        print(f"  Status: PRACTICING (no salary)")
else:
    print("  All employees are paid!")

print("\n" + "="*80)
print("SUMMARY FOR BUDGET INTEGRATION")
print("="*80)
print(f"\nTotal Employees: {all_employees.count()}")
print(f"Paid (for budget): {len(paid_employees)}")
print(f"Practicing (exclude from budget): {len(practicing_employees)}")

compliant_paid = [e for e in paid_employees if e['compliant']]
print(f"\nPaid & Compliant (include in payroll): {len(compliant_paid)}")
print(f"Paid & Non-compliant (hold payment): {len(paid_employees) - len(compliant_paid)}")

print("\n" + "="*80)
print("✅ Analysis Complete")
print("="*80)

