#!/usr/bin/env python3
"""
Setup Realistic Test Users for Request-Approval System

Creates 3 different user types:
1. Normal Staff - Can create requests, cannot approve
2. Admin - Can create requests and approve others' requests
3. Superuser - Full system access
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from finance.models import BudgetRequest, ApprovalPolicy, BudgetCategory, Department, DisbursementRequest, Company

User = get_user_model()

def create_test_users():
    """Create realistic test users with proper roles"""
    print('🔧 Setting up realistic test users...')
    
    with transaction.atomic():
        # 1. Normal Staff User (Can create requests, cannot approve)
        staff_user, created = User.objects.get_or_create(
            username='normal_staff',
            defaults={
                'email': 'normal.staff@test.com',
                'first_name': 'Normal',
                'last_name': 'Staff',
                'category': 2,  # Staff category
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
            }
        )
        if created:
            staff_user.set_password('testpass123')
            staff_user.save()
            print('✅ Created normal staff user')
        else:
            print('✅ Found existing normal staff user')
        
        # 2. Admin User (Can create requests and approve others')
        admin_user, created = User.objects.get_or_create(
            username='admin_user',
            defaults={
                'email': 'admin.user@test.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'category': 2,  # Staff category
                'is_staff': True,
                'is_superuser': False,
                'is_active': True,
                'email_verified': True,
            }
        )
        if created:
            admin_user.set_password('testpass123')
            admin_user.save()
            print('✅ Created admin user')
        else:
            print('✅ Found existing admin user')
        
        # 3. Superuser (Full system access)
        superuser, created = User.objects.get_or_create(
            username='superuser',
            defaults={
                'email': 'superuser@test.com',
                'first_name': 'Super',
                'last_name': 'User',
                'category': 2,  # Staff category
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'email_verified': True,
            }
        )
        if created:
            superuser.set_password('testpass123')
            superuser.save()
            print('✅ Created superuser')
        else:
            print('✅ Found existing superuser')
    
    return staff_user, admin_user, superuser

def setup_permissions():
    """Setup proper permissions for each user type"""
    print('\n🔐 Setting up role-based permissions...')
    
    # Get all finance-related permissions
    finance_models = [
        'finance.budgetrequest',
        'finance.approvalpolicy',
        'finance.disbursementrequest',
        'finance.automationauditlog',
        'main.company',
        'main.department'
    ]
    
    all_permissions = []
    for model in finance_models:
        try:
            app_label, model_name = model.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
            perms = Permission.objects.filter(content_type=ct)
            all_permissions.extend(perms)
        except:
            pass
    
    # Create groups
    staff_group, created = Group.objects.get_or_create(name='Staff Users')
    admin_group, created = Group.objects.get_or_create(name='Admin Users')
    superuser_group, created = Group.objects.get_or_create(name='Superusers')
    
    # Assign permissions to groups
    # Staff: Can create and view their own requests
    staff_permissions = [p for p in all_permissions if p.codename in [
        'add_budgetrequest', 'view_budgetrequest', 'change_budgetrequest',
        'view_company', 'view_department', 'view_budgetcategory'
    ]]
    staff_group.permissions.set(staff_permissions)
    
    # Admin: Can do everything staff can do + approve requests
    admin_permissions = all_permissions
    admin_group.permissions.set(admin_permissions)
    
    # Superuser: Already has all permissions
    
    # Assign users to groups
    staff_user = User.objects.get(username='normal_staff')
    admin_user = User.objects.get(username='admin_user')
    superuser = User.objects.get(username='superuser')
    
    staff_user.groups.add(staff_group)
    admin_user.groups.add(admin_group)
    superuser.groups.add(superuser_group)
    
    print(f'✅ Created {staff_group.permissions.count()} permissions for staff group')
    print(f'✅ Created {admin_group.permissions.count()} permissions for admin group')
    print(f'✅ Superuser has full access')

def setup_test_data():
    """Setup test data (companies, departments, categories, policies)"""
    print('\n🏢 Setting up test data...')
    
    # Create company
    company, created = Company.objects.get_or_create(
        name='Test Company Ltd',
        defaults={
            'slug': 'test-company-ltd',
            'description': 'Test company for realistic workflow testing'
        }
    )
    if created:
        print('✅ Created test company')
    else:
        print('✅ Found existing test company')
    
    # Create departments
    departments = [
        ('IT Department', 'Information Technology Department'),
        ('Finance Department', 'Financial Management Department'),
        ('HR Department', 'Human Resources Department'),
        ('Marketing Department', 'Marketing and Communications Department')
    ]
    
    created_departments = []
    for dept_name, dept_desc in departments:
        dept, created = Department.objects.get_or_create(
            name=dept_name,
            defaults={
                'company': company,
                'description': dept_desc
            }
        )
        created_departments.append(dept)
        if created:
            print(f'✅ Created department: {dept_name}')
        else:
            print(f'✅ Found existing department: {dept_name}')
    
    # Create budget categories
    categories = [
        'Software Development',
        'Hardware Procurement',
        'Marketing Campaigns',
        'Training and Development',
        'Office Supplies',
        'Travel and Entertainment'
    ]
    
    created_categories = []
    for cat_name in categories:
        cat, created = BudgetCategory.objects.get_or_create(
            name=cat_name,
            defaults={
                'description': f'Budget category for {cat_name.lower()}'
            }
        )
        created_categories.append(cat)
        if created:
            print(f'✅ Created budget category: {cat_name}')
        else:
            print(f'✅ Found existing budget category: {cat_name}')
    
    return company, created_departments, created_categories

def setup_approval_policies(admin_user, superuser, departments, categories):
    """Setup realistic approval policies"""
    print('\n📋 Setting up approval policies...')
    
    # Policy 1: Low amount requests (staff can approve)
    low_policy, created = ApprovalPolicy.objects.get_or_create(
        name='Low Amount Policy',
        defaults={
            'description': 'Policy for low amount requests (under $1,000)',
            'min_amount': Decimal('100.00'),
            'max_amount': Decimal('1000.00'),
            'approver_roles': ['admin', 'superuser'],
            'approval_chain': [
                {
                    'user_id': admin_user.id,
                    'role': 'admin',
                    'level': 1,
                    'required': True
                }
            ],
            'auto_approve': False,
            'requires_otp': False,
            'max_approval_days': 3,
            'escalation_days': 1,
            'applicable_user_types': ['Staff']
        }
    )
    
    # Policy 2: Medium amount requests (admin approval required)
    medium_policy, created = ApprovalPolicy.objects.get_or_create(
        name='Medium Amount Policy',
        defaults={
            'description': 'Policy for medium amount requests ($1,000 - $10,000)',
            'min_amount': Decimal('1000.00'),
            'max_amount': Decimal('10000.00'),
            'approver_roles': ['admin', 'superuser'],
            'approval_chain': [
                {
                    'user_id': admin_user.id,
                    'role': 'admin',
                    'level': 1,
                    'required': True
                }
            ],
            'auto_approve': False,
            'requires_otp': True,
            'max_approval_days': 5,
            'escalation_days': 2,
            'applicable_user_types': ['Staff']
        }
    )
    
    # Policy 3: High amount requests (superuser approval required)
    high_policy, created = ApprovalPolicy.objects.get_or_create(
        name='High Amount Policy',
        defaults={
            'description': 'Policy for high amount requests (over $10,000)',
            'min_amount': Decimal('10000.00'),
            'max_amount': Decimal('100000.00'),
            'approver_roles': ['superuser'],
            'approval_chain': [
                {
                    'user_id': superuser.id,
                    'role': 'superuser',
                    'level': 1,
                    'required': True
                }
            ],
            'auto_approve': False,
            'requires_otp': True,
            'max_approval_days': 7,
            'escalation_days': 3,
            'applicable_user_types': ['Staff']
        }
    )
    
    # Add departments and categories to policies
    for policy in [low_policy, medium_policy, high_policy]:
        for dept in departments:
            policy.applicable_departments.add(dept)
        for cat in categories:
            policy.applicable_categories.add(cat)
    
    print(f'✅ Created {3} approval policies')
    return [low_policy, medium_policy, high_policy]

def main():
    """Main setup function"""
    print('🚀 Setting up Realistic Test Environment')
    print('=' * 60)
    
    # Create users
    staff_user, admin_user, superuser = create_test_users()
    
    # Setup permissions
    setup_permissions()
    
    # Setup test data
    company, departments, categories = setup_test_data()
    
    # Setup approval policies
    policies = setup_approval_policies(admin_user, superuser, departments, categories)
    
    print('\n📊 Test Environment Summary')
    print('=' * 60)
    print(f'👤 Normal Staff User: {staff_user.username} / testpass123')
    print(f'   - Can create budget requests')
    print(f'   - Cannot approve requests')
    print(f'   - Department: {staff_user.category}')
    
    print(f'\n👨‍💼 Admin User: {admin_user.username} / testpass123')
    print(f'   - Can create budget requests')
    print(f'   - Can approve low and medium amount requests')
    print(f'   - Cannot approve high amount requests')
    
    print(f'\n👑 Superuser: {superuser.username} / testpass123')
    print(f'   - Can create budget requests')
    print(f'   - Can approve all requests')
    print(f'   - Full system access')
    
    print(f'\n🏢 Test Data:')
    print(f'   - Company: {company.name}')
    print(f'   - Departments: {len(departments)}')
    print(f'   - Budget Categories: {len(categories)}')
    print(f'   - Approval Policies: {len(policies)}')
    
    print(f'\n🎯 Test Scenarios:')
    print(f'   1. Normal staff creates $500 request → Admin approves')
    print(f'   2. Normal staff creates $5,000 request → Admin approves')
    print(f'   3. Normal staff creates $15,000 request → Superuser approves')
    print(f'   4. Admin creates $2,000 request → Admin approves own request')
    print(f'   5. Superuser creates $20,000 request → Superuser approves')
    
    print(f'\n✅ Setup Complete! Ready for realistic testing.')
    
    return staff_user, admin_user, superuser, company, departments, categories, policies

if __name__ == "__main__":
    main()
