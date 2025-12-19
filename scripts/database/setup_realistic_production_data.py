#!/usr/bin/env python3
"""
Setup Realistic Production Data for Budget Request System

Creates realistic companies, departments, categories, and users
Removes all dummy/test data
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
from finance.models import BudgetRequest, ApprovalPolicy, BudgetCategory, DisbursementRequest, AutomationAuditLog
from accounts.models import Department
from main.models import Company

User = get_user_model()

def cleanup_dummy_data():
    """Remove all dummy/test data"""
    print('🧹 Cleaning up dummy data...')
    print('=' * 50)
    
    # Delete dummy budget requests (simplified approach)
    test_requests = BudgetRequest.objects.filter(purpose__icontains='test')
    dummy_requests = BudgetRequest.objects.filter(purpose__icontains='dummy')
    test_cost_centers = BudgetRequest.objects.filter(cost_center__icontains='test')
    dummy_cost_centers = BudgetRequest.objects.filter(cost_center__icontains='dummy')
    
    total_deleted = 0
    for queryset in [test_requests, dummy_requests, test_cost_centers, dummy_cost_centers]:
        count = queryset.count()
        queryset.delete()
        total_deleted += count
    
    print(f'✅ Deleted {total_deleted} dummy budget requests')
    
    # Delete dummy departments
    test_depts = Department.objects.filter(name__icontains='test')
    dummy_depts = Department.objects.filter(name__icontains='dummy')
    
    total_deleted = 0
    for queryset in [test_depts, dummy_depts]:
        count = queryset.count()
        queryset.delete()
        total_deleted += count
    
    print(f'✅ Deleted {total_deleted} dummy departments')
    
    # Delete dummy companies
    test_companies = Company.objects.filter(name__icontains='test')
    dummy_companies = Company.objects.filter(name__icontains='dummy')
    
    total_deleted = 0
    for queryset in [test_companies, dummy_companies]:
        count = queryset.count()
        queryset.delete()
        total_deleted += count
    
    print(f'✅ Deleted {total_deleted} dummy companies')
    
    # Delete dummy budget categories
    test_categories = BudgetCategory.objects.filter(name__icontains='test')
    dummy_categories = BudgetCategory.objects.filter(name__icontains='dummy')
    
    total_deleted = 0
    for queryset in [test_categories, dummy_categories]:
        count = queryset.count()
        queryset.delete()
        total_deleted += count
    
    print(f'✅ Deleted {total_deleted} dummy budget categories')

def create_realistic_companies():
    """Create realistic companies"""
    print('\n🏢 Creating realistic companies...')
    print('=' * 50)
    
    companies_data = [
        {
            'name': 'Coda Analytics Ltd',
            'slug': 'coda-analytics-ltd',
            'description': 'Leading analytics and data science consulting firm'
        },
        {
            'name': 'TechFlow Solutions',
            'slug': 'techflow-solutions',
            'description': 'Software development and IT consulting company'
        },
        {
            'name': 'Green Energy Corp',
            'slug': 'green-energy-corp',
            'description': 'Renewable energy solutions and sustainability consulting'
        }
    ]
    
    created_companies = []
    for company_data in companies_data:
        company, created = Company.objects.get_or_create(
            slug=company_data['slug'],
            defaults=company_data
        )
        if created:
            print(f'✅ Created company: {company.name}')
        else:
            print(f'✅ Found existing company: {company.name}')
        created_companies.append(company)
    
    return created_companies

def create_realistic_departments(companies):
    """Create realistic departments"""
    print('\n🏬 Creating realistic departments...')
    print('=' * 50)
    
    # Use the predefined department choices from the model
    departments_data = [
        {
            'name': 'HR Department',
            'description': 'Human Resources and Employee Management',
            'slug': 'hr-department'
        },
        {
            'name': 'IT Department',
            'description': 'Information Technology and Technical Support',
            'slug': 'it-department'
        },
        {
            'name': 'Marketing Department',
            'description': 'Marketing, Advertising, and Brand Management',
            'slug': 'marketing-department'
        },
        {
            'name': 'Finance Department',
            'description': 'Financial Management and Budget Planning',
            'slug': 'finance-department'
        },
        {
            'name': 'Security Department',
            'description': 'Information Security and Risk Management',
            'slug': 'security-department'
        },
        {
            'name': 'Management Department',
            'description': 'Executive Management and Strategic Planning',
            'slug': 'management-department'
        },
        {
            'name': 'Health Department',
            'description': 'Employee Health and Wellness Programs',
            'slug': 'health-department'
        }
    ]
    
    created_departments = []
    for dept_data in departments_data:
        department, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={
                'description': dept_data['description'],
                'slug': dept_data['slug']
            }
        )
        if created:
            print(f'✅ Created department: {department.name}')
        else:
            print(f'✅ Found existing department: {department.name}')
        created_departments.append(department)
    
    return created_departments

def create_realistic_budget_categories():
    """Create realistic budget categories"""
    print('\n📊 Creating realistic budget categories...')
    print('=' * 50)
    
    categories_data = [
        'Software Development',
        'Hardware & Infrastructure',
        'Marketing & Advertising',
        'Training & Development',
        'Travel & Conferences',
        'Office Supplies & Equipment',
        'Research & Development',
        'Legal & Compliance',
        'Utilities & Facilities',
        'Professional Services',
        'Equipment & Machinery',
        'Security & IT Services'
    ]
    
    created_categories = []
    for cat_name in categories_data:
        category, created = BudgetCategory.objects.get_or_create(
            name=cat_name,
            defaults={'description': f'Budget category for {cat_name.lower()}'}
        )
        if created:
            print(f'✅ Created category: {category.name}')
        else:
            print(f'✅ Found existing category: {category.name}')
        created_categories.append(category)
    
    return created_categories

def create_realistic_users():
    """Create realistic users with proper roles"""
    print('\n👥 Creating realistic users...')
    print('=' * 50)
    
    users_data = [
        # Staff Users
        {
            'username': 'sarah.johnson',
            'email': 'sarah.johnson@coda-analytics.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'category': 2,  # Staff
            'is_staff': True,
            'is_superuser': False,
            'password': 'SecurePass123!'
        },
        {
            'username': 'michael.chen',
            'email': 'michael.chen@coda-analytics.com',
            'first_name': 'Michael',
            'last_name': 'Chen',
            'category': 2,  # Staff
            'is_staff': True,
            'is_superuser': False,
            'password': 'SecurePass123!'
        },
        {
            'username': 'emma.rodriguez',
            'email': 'emma.rodriguez@coda-analytics.com',
            'first_name': 'Emma',
            'last_name': 'Rodriguez',
            'category': 2,  # Staff
            'is_staff': True,
            'is_superuser': False,
            'password': 'SecurePass123!'
        },
        
        # Admin Users
        {
            'username': 'david.kim',
            'email': 'david.kim@coda-analytics.com',
            'first_name': 'David',
            'last_name': 'Kim',
            'category': 2,  # Staff
            'is_staff': True,
            'is_superuser': False,
            'password': 'AdminPass123!'
        },
        {
            'username': 'lisa.thompson',
            'email': 'lisa.thompson@coda-analytics.com',
            'first_name': 'Lisa',
            'last_name': 'Thompson',
            'category': 2,  # Staff
            'is_staff': True,
            'is_superuser': False,
            'password': 'AdminPass123!'
        },
        
        # Superuser
        {
            'username': 'admin',
            'email': 'admin@coda-analytics.com',
            'first_name': 'System',
            'last_name': 'Administrator',
            'category': 2,  # Staff
            'is_staff': True,
            'is_superuser': True,
            'password': 'SuperAdmin123!'
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'category': user_data['category'],
                'is_staff': user_data['is_staff'],
                'is_superuser': user_data['is_superuser'],
                'is_active': True,
                'email_verified': True,
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f'✅ Created user: {user.username} ({user.get_full_name()})')
        else:
            print(f'✅ Found existing user: {user.username} ({user.get_full_name()})')
        created_users.append(user)
    
    return created_users

def setup_user_permissions(users):
    """Setup proper permissions for users"""
    print('\n🔐 Setting up user permissions...')
    print('=' * 50)
    
    # Create groups
    staff_group, created = Group.objects.get_or_create(name='Staff Users')
    admin_group, created = Group.objects.get_or_create(name='Admin Users')
    
    # Get all finance permissions
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
    
    # Staff permissions (limited)
    staff_permissions = [p for p in all_permissions if p.codename in [
        'add_budgetrequest', 'view_budgetrequest', 'change_budgetrequest',
        'view_company', 'view_department', 'view_budgetcategory'
    ]]
    staff_group.permissions.set(staff_permissions)
    
    # Admin permissions (extended)
    admin_permissions = all_permissions
    admin_group.permissions.set(admin_permissions)
    
    # Assign users to groups
    staff_users = [u for u in users if not u.is_superuser and 'admin' not in u.username.lower()]
    admin_users = [u for u in users if 'admin' in u.username.lower() or u.is_superuser]
    
    for user in staff_users:
        user.groups.add(staff_group)
        print(f'✅ Added {user.username} to Staff group')
    
    for user in admin_users:
        user.groups.add(admin_group)
        print(f'✅ Added {user.username} to Admin group')

def create_realistic_approval_policies(admin_users, departments, categories):
    """Create realistic approval policies"""
    print('\n📋 Creating realistic approval policies...')
    print('=' * 50)
    
    # Policy 1: Low amount requests (staff can approve)
    low_policy, created = ApprovalPolicy.objects.get_or_create(
        name='Low Amount Policy',
        defaults={
            'description': 'Policy for low amount requests (under $2,500)',
            'min_amount': Decimal('100.00'),
            'max_amount': Decimal('2500.00'),
            'approver_roles': ['admin', 'superuser'],
            'approval_chain': [
                {
                    'user_id': admin_users[0].id,
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
            'description': 'Policy for medium amount requests ($2,500 - $15,000)',
            'min_amount': Decimal('2500.00'),
            'max_amount': Decimal('15000.00'),
            'approver_roles': ['admin', 'superuser'],
            'approval_chain': [
                {
                    'user_id': admin_users[0].id,
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
            'description': 'Policy for high amount requests (over $15,000)',
            'min_amount': Decimal('15000.00'),
            'max_amount': Decimal('100000.00'),
            'approver_roles': ['superuser'],
            'approval_chain': [
                {
                    'user_id': admin_users[-1].id,  # Superuser
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

def create_realistic_budget_requests(users, departments, categories):
    """Create realistic budget requests"""
    print('\n💰 Creating realistic budget requests...')
    print('=' * 50)
    
    requests_data = [
        {
            'requester': users[0],  # Sarah Johnson
            'amount': Decimal('1500.00'),
            'purpose': 'Software licenses for Q1 development projects',
            'department': departments[1],  # Software Engineering
            'budget_category': categories[0],  # Software Development
            'priority': 'medium',
            'cost_center': 'SW-DEV-2024-Q1',
            'status': 'draft'
        },
        {
            'requester': users[1],  # Michael Chen
            'amount': Decimal('8500.00'),
            'purpose': 'High-performance computing hardware for data analysis',
            'department': departments[0],  # Data Science
            'budget_category': categories[1],  # Hardware & Infrastructure
            'priority': 'high',
            'cost_center': 'DS-HPC-2024',
            'status': 'submitted'
        },
        {
            'requester': users[2],  # Emma Rodriguez
            'amount': Decimal('3200.00'),
            'purpose': 'Marketing campaign for new product launch',
            'department': departments[2],  # Business Intelligence
            'budget_category': categories[2],  # Marketing & Advertising
            'priority': 'high',
            'cost_center': 'BI-MKT-2024-Q2',
            'status': 'submitted'
        },
        {
            'requester': users[0],  # Sarah Johnson
            'amount': Decimal('1200.00'),
            'purpose': 'Team training and certification programs',
            'department': departments[1],  # Software Engineering
            'budget_category': categories[3],  # Training & Development
            'priority': 'medium',
            'cost_center': 'SW-TRAIN-2024',
            'status': 'approved'
        },
        {
            'requester': users[1],  # Michael Chen
            'amount': Decimal('25000.00'),
            'purpose': 'Advanced analytics platform and cloud infrastructure',
            'department': departments[0],  # Data Science
            'budget_category': categories[1],  # Hardware & Infrastructure
            'priority': 'urgent',
            'cost_center': 'DS-PLATFORM-2024',
            'status': 'under_review'
        }
    ]
    
    created_requests = []
    for req_data in requests_data:
        request, created = BudgetRequest.objects.get_or_create(
            requester=req_data['requester'],
            purpose=req_data['purpose'],
            defaults={
                'amount': req_data['amount'],
                'currency': 'USD',
                'department': req_data['department'],
                'budget_category': req_data['budget_category'],
                'required_date': timezone.now().date() + timedelta(days=30),
                'priority': req_data['priority'],
                'cost_center': req_data['cost_center'],
                'attachments': [],
                'request_date': timezone.now(),
                'approval_chain': [],
                'status': req_data['status'],
                'created_by': req_data['requester'],
                'last_modified_by': req_data['requester']
            }
        )
        if created:
            print(f'✅ Created request: {request.purpose[:50]}... (${request.amount})')
        else:
            print(f'✅ Found existing request: {request.purpose[:50]}... (${request.amount})')
        created_requests.append(request)
    
    return created_requests

def fix_approval_chains(requests, admin_users):
    """Fix approval chains for submitted requests"""
    print('\n🔧 Fixing approval chains...')
    print('=' * 50)
    
    for request in requests:
        if request.status in ['submitted', 'under_review']:
            # Set up proper approval chain
            approver = admin_users[0] if request.amount < Decimal('15000') else admin_users[-1]
            
            request.approval_chain = [
                {
                    'user_id': approver.id,
                    'role': 'admin' if not approver.is_superuser else 'superuser',
                    'level': 1,
                    'required': True,
                    'status': 'pending'
                }
            ]
            request.current_approver = approver
            request.save()
            print(f'✅ Fixed approval chain for request {request.id} (${request.amount})')

def main():
    """Main setup function"""
    print('🚀 Setting up Realistic Production Data')
    print('=' * 60)
    
    with transaction.atomic():
        # Step 1: Clean up dummy data
        cleanup_dummy_data()
        
        # Step 2: Create realistic data
        companies = create_realistic_companies()
        departments = create_realistic_departments(companies)
        categories = create_realistic_budget_categories()
        users = create_realistic_users()
        
        # Step 3: Setup permissions
        setup_user_permissions(users)
        
        # Step 4: Create approval policies
        policies = create_realistic_approval_policies(users, departments, categories)
        
        # Step 5: Create budget requests
        requests = create_realistic_budget_requests(users, departments, categories)
        
        # Step 6: Fix approval chains
        fix_approval_chains(requests, users)
    
    print('\n📊 Production Data Summary')
    print('=' * 60)
    print(f'🏢 Companies: {Company.objects.count()}')
    print(f'🏬 Departments: {Department.objects.count()}')
    print(f'📊 Budget Categories: {BudgetCategory.objects.count()}')
    print(f'👥 Users: {User.objects.count()}')
    print(f'📋 Approval Policies: {ApprovalPolicy.objects.count()}')
    print(f'💰 Budget Requests: {BudgetRequest.objects.count()}')
    
    print(f'\n🎯 Test Users:')
    print(f'   Staff: sarah.johnson / SecurePass123!')
    print(f'   Staff: michael.chen / SecurePass123!')
    print(f'   Staff: emma.rodriguez / SecurePass123!')
    print(f'   Admin: david.kim / AdminPass123!')
    print(f'   Admin: lisa.thompson / AdminPass123!')
    print(f'   Superuser: admin / SuperAdmin123!')
    
    print(f'\n✅ Production data setup complete!')
    print(f'   - All dummy data removed')
    print(f'   - Realistic companies and departments created')
    print(f'   - Proper user roles and permissions set')
    print(f'   - Approval chains configured correctly')

if __name__ == "__main__":
    main()
