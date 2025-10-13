#!/usr/bin/env python3
"""
Local testing environment setup script for CODA automation system
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda.settings')
django.setup()

from accounts.models import Department
from finance.models import BudgetRequest, ApprovalPolicy, DisbursementRequest, AutomationAuditLog, BudgetCategory

User = get_user_model()


def create_test_data():
    """Create comprehensive test data for local testing"""
    
    print("🔧 Setting up local testing environment...")
    
    # Create test users
    print("👥 Creating test users...")
    
    # Regular user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created user: {user.username}")
    else:
        print(f"ℹ️  User already exists: {user.username}")
    
    # Manager user
    manager, created = User.objects.get_or_create(
        username='manager',
        defaults={
            'email': 'manager@example.com',
            'first_name': 'Jane',
            'last_name': 'Manager',
            'is_staff': True,
            'is_active': True
        }
    )
    if created:
        manager.set_password('testpass123')
        manager.save()
        print(f"✅ Created manager: {manager.username}")
    else:
        print(f"ℹ️  Manager already exists: {manager.username}")
    
    # Admin user
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    if created:
        admin.set_password('adminpass123')
        admin.save()
        print(f"✅ Created admin: {admin.username}")
    else:
        print(f"ℹ️  Admin already exists: {admin.username}")
    
    # Create test departments
    print("🏢 Creating test departments...")
    
    departments = [
        {'name': 'Finance', 'description': 'Finance department'},
        {'name': 'IT', 'description': 'Information Technology department'},
        {'name': 'HR', 'description': 'Human Resources department'},
        {'name': 'Operations', 'description': 'Operations department'},
        {'name': 'Marketing', 'description': 'Marketing department'}
    ]
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'description': dept_data['description']}
        )
        if created:
            print(f"✅ Created department: {dept.name}")
        else:
            print(f"ℹ️  Department already exists: {dept.name}")
    
    # Create test budget categories
    print("📊 Creating test budget categories...")
    
    categories = [
        {'name': 'Office Supplies', 'description': 'Office supplies and equipment'},
        {'name': 'Travel', 'description': 'Business travel expenses'},
        {'name': 'Training', 'description': 'Employee training and development'},
        {'name': 'Software', 'description': 'Software licenses and subscriptions'},
        {'name': 'Marketing', 'description': 'Marketing and advertising expenses'},
        {'name': 'Equipment', 'description': 'Office equipment and furniture'},
        {'name': 'Utilities', 'description': 'Utilities and office expenses'},
        {'name': 'Professional Services', 'description': 'Consulting and professional services'}
    ]
    
    for cat_data in categories:
        category, created = BudgetCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f"✅ Created category: {category.name}")
        else:
            print(f"ℹ️  Category already exists: {category.name}")
    
    # Create test approval policies
    print("📋 Creating test approval policies...")
    
    policies = [
        {
            'name': 'Low Value Policy',
            'description': 'Policy for low value requests',
            'min_amount': Decimal('0.00'),
            'max_amount': Decimal('100.00'),
            'approver_roles': ['Manager'],
            'auto_approve': True,
            'requires_otp': False,
            'applicable_user_types': ['Staff'],
            'max_approval_days': 1,
            'escalation_days': 1
        },
        {
            'name': 'Medium Value Policy',
            'description': 'Policy for medium value requests',
            'min_amount': Decimal('100.01'),
            'max_amount': Decimal('1000.00'),
            'approver_roles': ['Manager', 'Director'],
            'auto_approve': False,
            'requires_otp': True,
            'applicable_user_types': ['Staff'],
            'max_approval_days': 3,
            'escalation_days': 2
        },
        {
            'name': 'High Value Policy',
            'description': 'Policy for high value requests',
            'min_amount': Decimal('1000.01'),
            'max_amount': Decimal('10000.00'),
            'approver_roles': ['Manager', 'Director', 'CEO'],
            'auto_approve': False,
            'requires_otp': True,
            'applicable_user_types': ['Staff'],
            'max_approval_days': 7,
            'escalation_days': 3
        }
    ]
    
    for policy_data in policies:
        policy, created = ApprovalPolicy.objects.get_or_create(
            name=policy_data['name'],
            defaults=policy_data
        )
        if created:
            # Add all departments and categories
            policy.applicable_departments.set(Department.objects.all())
            policy.applicable_categories.set(BudgetCategory.objects.all())
            print(f"✅ Created policy: {policy.name}")
        else:
            print(f"ℹ️  Policy already exists: {policy.name}")
    
    # Create test budget requests
    print("💰 Creating test budget requests...")
    
    finance_dept = Department.objects.get(name='Finance')
    it_dept = Department.objects.get(name='IT')
    office_supplies = BudgetCategory.objects.get(name='Office Supplies')
    software = BudgetCategory.objects.get(name='Software')
    
    test_requests = [
        {
            'requester': user,
            'amount': Decimal('50.00'),
            'currency': 'USD',
            'purpose': 'Office supplies for Q1',
            'department': finance_dept,
            'budget_category': office_supplies,
            'priority': 'low',
            'status': 'draft'
        },
        {
            'requester': user,
            'amount': Decimal('500.00'),
            'currency': 'USD',
            'purpose': 'Software license renewal',
            'department': it_dept,
            'budget_category': software,
            'priority': 'medium',
            'status': 'submitted'
        },
        {
            'requester': user,
            'amount': Decimal('1500.00'),
            'currency': 'USD',
            'purpose': 'New server equipment',
            'department': it_dept,
            'budget_category': software,
            'priority': 'high',
            'status': 'under_review'
        }
    ]
    
    for i, req_data in enumerate(test_requests):
        request, created = BudgetRequest.objects.get_or_create(
            requester=req_data['requester'],
            amount=req_data['amount'],
            purpose=req_data['purpose'],
            defaults={
                **req_data,
                'required_date': date.today() + timedelta(days=30),
                'created_by': user,
                'last_modified_by': user
            }
        )
        if created:
            print(f"✅ Created request: {request.purpose} - ${request.amount}")
        else:
            print(f"ℹ️  Request already exists: {request.purpose}")
    
    # Create test disbursement requests
    print("💳 Creating test disbursement requests...")
    
    approved_request = BudgetRequest.objects.filter(status='under_review').first()
    if approved_request:
        disbursement, created = DisbursementRequest.objects.get_or_create(
            budget_request=approved_request,
            defaults={
                'disbursement_method': 'mpesa',
                'recipient_name': 'John Doe',
                'recipient_phone': '254712345678',
                'recipient_email': 'john@example.com',
                'amount': approved_request.amount,
                'currency': approved_request.currency,
                'status': 'pending'
            }
        )
        if created:
            print(f"✅ Created disbursement: {disbursement.recipient_name} - ${disbursement.amount}")
        else:
            print(f"ℹ️  Disbursement already exists: {disbursement.recipient_name}")
    
    # Create test audit logs
    print("📝 Creating test audit logs...")
    
    audit_actions = [
        ('budget_request_created', 'create'),
        ('budget_request_submitted', 'update'),
        ('budget_request_approved', 'update'),
        ('disbursement_created', 'create'),
        ('disbursement_processed', 'update'),
        ('user_login', 'create'),
        ('user_logout', 'create')
    ]
    
    for action, action_type in audit_actions:
        log, created = AutomationAuditLog.objects.get_or_create(
            action=action,
            action_type=action_type,
            user=user,
            defaults={
                'description': f'Test {action} action',
                'ip_address': '127.0.0.1',
                'user_agent': 'Test User Agent',
                'details': {'test': 'data'},
                'success': True
            }
        )
        if created:
            print(f"✅ Created audit log: {action}")
        else:
            print(f"ℹ️  Audit log already exists: {action}")
    
    print("\n🎉 Local testing environment setup complete!")
    print("\n📋 Test Data Summary:")
    print(f"   👥 Users: {User.objects.count()}")
    print(f"   🏢 Departments: {Department.objects.count()}")
    print(f"   📊 Budget Categories: {BudgetCategory.objects.count()}")
    print(f"   📋 Approval Policies: {ApprovalPolicy.objects.count()}")
    print(f"   💰 Budget Requests: {BudgetRequest.objects.count()}")
    print(f"   💳 Disbursement Requests: {DisbursementRequest.objects.count()}")
    print(f"   📝 Audit Logs: {AutomationAuditLog.objects.count()}")
    
    print("\n🔑 Test Credentials:")
    print("   👤 Regular User: testuser / testpass123")
    print("   👨‍💼 Manager: manager / testpass123")
    print("   👑 Admin: admin / adminpass123")
    
    print("\n🚀 Next Steps:")
    print("   1. Run migrations: python manage.py migrate")
    print("   2. Start development server: python manage.py runserver")
    print("   3. Access admin: http://localhost:8000/admin/")
    print("   4. Access API: http://localhost:8000/api/v1/")
    print("   5. Run tests: python manage.py test finance.tests")


def run_tests():
    """Run all automation system tests"""
    
    print("🧪 Running automation system tests...")
    
    # Run model tests
    print("\n📊 Running model tests...")
    execute_from_command_line(['manage.py', 'test', 'finance.tests.test_automation_models'])
    
    # Run service tests
    print("\n🔧 Running service tests...")
    execute_from_command_line(['manage.py', 'test', 'finance.tests.test_automation_services'])
    
    # Run API tests
    print("\n🌐 Running API tests...")
    execute_from_command_line(['manage.py', 'test', 'finance.tests.test_automation_api'])
    
    # Run email template tests
    print("\n📧 Running email template tests...")
    execute_from_command_line(['manage.py', 'test', 'finance.tests.test_email_templates'])
    
    # Run integration tests
    print("\n🔗 Running integration tests...")
    execute_from_command_line(['manage.py', 'test', 'finance.tests.test_automation_integration'])
    
    print("\n✅ All tests completed!")


def cleanup_test_data():
    """Clean up test data"""
    
    print("🧹 Cleaning up test data...")
    
    # Delete test data in reverse order of dependencies
    AutomationAuditLog.objects.filter(user__username__in=['testuser', 'manager', 'admin']).delete()
    DisbursementRequest.objects.all().delete()
    BudgetRequest.objects.all().delete()
    ApprovalPolicy.objects.all().delete()
    BudgetCategory.objects.all().delete()
    Department.objects.all().delete()
    User.objects.filter(username__in=['testuser', 'manager', 'admin']).delete()
    
    print("✅ Test data cleaned up!")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'setup':
            create_test_data()
        elif command == 'test':
            run_tests()
        elif command == 'cleanup':
            cleanup_test_data()
        elif command == 'reset':
            cleanup_test_data()
            create_test_data()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: setup, test, cleanup, reset")
    else:
        print("🔧 CODA Automation System - Local Testing Setup")
        print("\nUsage:")
        print("  python setup_local_testing.py setup   - Create test data")
        print("  python setup_local_testing.py test    - Run all tests")
        print("  python setup_local_testing.py cleanup - Remove test data")
        print("  python setup_local_testing.py reset   - Clean and recreate test data")


if __name__ == '__main__':
    main()
