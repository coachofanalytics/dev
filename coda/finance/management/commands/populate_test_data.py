"""
Django management command to populate test data for the enhanced budget system

This command creates realistic test data including:
- Sample companies and departments
- Historical transaction data (6 months)
- Various budget types and timeframes
- Budget estimation templates
- Multi-year budget plans
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random

from main.models import Companyas
from accounts.models import Department
from finance.models import (
    Budget, BudgetCategory, BudgetSubCategory, Transaction,
    BudgetEstimationTemplate, MultiYearBudgetPlan
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate test data for enhanced budget system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing test data...')
            self.clear_test_data()

        self.stdout.write('Creating test data for enhanced budget system...')
        
        # Create companies and departments
        companies = self.create_companies()
        departments = self.create_departments()
        users = self.create_users()
        
        # Create budget categories and subcategories
        categories = self.create_budget_categories()
        
        # Create historical transaction data (6 months)
        self.create_historical_transactions(companies, departments, categories, users)
        
        # Create various budget types
        self.create_sample_budgets(companies, departments, categories, users)
        
        # Create budget estimation templates
        self.create_estimation_templates()
        
        # Create multi-year budget plans
        self.create_multi_year_plans(companies, departments, users)
        
        # Create approval policies
        self.create_approval_policies()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated test data!')
        )

    def clear_test_data(self):
        """Clear existing test data"""
        # Clear test transactions
        Transaction.objects.filter(description__icontains='TEST').delete()
        
        # Clear test budgets
        Budget.objects.filter(description__icontains='TEST').delete()
        
        # Clear test templates
        BudgetEstimationTemplate.objects.filter(name__icontains='Test').delete()
        
        # Clear test plans
        MultiYearBudgetPlan.objects.filter(name__icontains='Test').delete()

    def create_companies(self):
        """Create sample companies"""
        companies = []
        
        # CODA (main company)
        company, created = Company.objects.get_or_create(
            slug='coda',
            defaults={
                'name': 'CODA Technologies',
                'description': 'Leading technology solutions provider',
                'is_featured': True,
            }
        )
        companies.append(company)
        
        # Client companies
        client_companies = [
            {'slug': 'acme-corp', 'name': 'ACME Corporation', 'description': 'Manufacturing company'},
            {'slug': 'tech-startup', 'name': 'TechStart Inc', 'description': 'Technology startup'},
            {'slug': 'retail-chain', 'name': 'RetailMax Ltd', 'description': 'Retail chain'},
        ]
        
        for company_data in client_companies:
            company, created = Company.objects.get_or_create(
                slug=company_data['slug'],
                defaults=company_data
            )
            companies.append(company)
        
        self.stdout.write(f'Created {len(companies)} companies')
        return companies

    def create_departments(self):
        """Create sample departments"""
        departments = []
        
        # Use existing department choices
        department_choices = [
            ('IT Department', 'it-department', 'Software development team'),
            ('Marketing Department', 'marketing-department', 'Marketing and sales team'),
            ('Finance Department', 'finance-department', 'Finance and accounting'),
            ('HR Department', 'hr-department', 'Human resources'),
            ('Management Department', 'management-department', 'Management and administration'),
        ]
        
        for name, slug, description in department_choices:
            department, created = Department.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                }
            )
            departments.append(department)
        
        self.stdout.write(f'Created {len(departments)} departments')
        return departments

    def create_users(self):
        """Create sample users"""
        users = []
        
        # Create staff users
        staff_users = [
            {'username': 'admin', 'email': 'admin@coda.com', 'first_name': 'Admin', 'last_name': 'User'},
            {'username': 'finance_manager', 'email': 'finance@coda.com', 'first_name': 'Finance', 'last_name': 'Manager'},
            {'username': 'dev_lead', 'email': 'dev@coda.com', 'first_name': 'Dev', 'last_name': 'Lead'},
            {'username': 'marketing_head', 'email': 'marketing@coda.com', 'first_name': 'Marketing', 'last_name': 'Head'},
        ]
        
        for user_data in staff_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    **user_data,
                    'is_staff': True,
                    'is_active': True,
                    'category': 2,  # Staff category
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        self.stdout.write(f'Created {len(users)} users')
        return users

    def create_budget_categories(self):
        """Create budget categories and subcategories"""
        categories = []
        
        category_data = [
            {
                'name': 'Operations',
                'subcategories': ['Office Supplies', 'Utilities', 'Rent', 'Insurance']
            },
            {
                'name': 'Technology',
                'subcategories': ['Software Licenses', 'Hardware', 'Cloud Services', 'Maintenance']
            },
            {
                'name': 'Marketing',
                'subcategories': ['Digital Marketing', 'Print Advertising', 'Events', 'Branding']
            },
            {
                'name': 'Development',
                'subcategories': ['Development Tools', 'Third-party Services', 'Testing', 'Deployment']
            },
            {
                'name': 'Personnel',
                'subcategories': ['Salaries', 'Benefits', 'Training', 'Recruitment']
            },
        ]
        
        for cat_data in category_data:
            category, created = BudgetCategory.objects.get_or_create(
                name=cat_data['name']
            )
            categories.append(category)
            
            # Create subcategories
            for subcat_name in cat_data['subcategories']:
                BudgetSubCategory.objects.get_or_create(
                    name=subcat_name,
                    category=category
                )
        
        self.stdout.write(f'Created {len(categories)} budget categories')
        return categories

    def create_historical_transactions(self, companies, departments, categories, users):
        """Create 6 months of historical transaction data"""
        transactions = []
        start_date = timezone.now() - timedelta(days=180)  # 6 months ago
        
        # Transaction patterns by category
        transaction_patterns = {
            'Operations': {
                'amounts': [50, 100, 200, 500, 1000],
                'frequencies': [0.3, 0.4, 0.2, 0.08, 0.02],  # More frequent smaller amounts
                'descriptions': [
                    'Office supplies purchase',
                    'Utility bill payment',
                    'Rent payment',
                    'Insurance premium',
                    'Office maintenance'
                ]
            },
            'Technology': {
                'amounts': [100, 500, 1000, 2500, 5000],
                'frequencies': [0.2, 0.3, 0.3, 0.15, 0.05],
                'descriptions': [
                    'Software license renewal',
                    'Cloud service subscription',
                    'Hardware upgrade',
                    'Development tool purchase',
                    'IT maintenance'
                ]
            },
            'Marketing': {
                'amounts': [200, 1000, 2500, 5000, 10000],
                'frequencies': [0.1, 0.3, 0.4, 0.15, 0.05],
                'descriptions': [
                    'Social media advertising',
                    'Google Ads campaign',
                    'Print advertising',
                    'Event sponsorship',
                    'Brand campaign'
                ]
            },
            'Development': {
                'amounts': [500, 1500, 3000, 7500, 15000],
                'frequencies': [0.15, 0.25, 0.35, 0.2, 0.05],
                'descriptions': [
                    'Third-party API subscription',
                    'Development tool license',
                    'Testing service',
                    'Deployment service',
                    'Code review service'
                ]
            },
            'Personnel': {
                'amounts': [2000, 5000, 10000, 20000, 50000],
                'frequencies': [0.05, 0.1, 0.3, 0.4, 0.15],
                'descriptions': [
                    'Employee training',
                    'Benefits payment',
                    'Salary payment',
                    'Recruitment cost',
                    'Performance bonus'
                ]
            }
        }
        
        # Generate transactions for each day
        current_date = start_date
        while current_date <= timezone.now():
            # Skip weekends for business transactions
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                # Generate 1-5 transactions per day
                num_transactions = random.randint(1, 5)
                
                for _ in range(num_transactions):
                    # Select random category
                    category = random.choice(categories)
                    subcategory = random.choice(category.subcategories.all())
                    
                    # Get transaction pattern
                    pattern = transaction_patterns.get(category.name, transaction_patterns['Operations'])
                    
                    # Select amount based on frequency
                    amount = random.choices(pattern['amounts'], weights=pattern['frequencies'])[0]
                    description = random.choice(pattern['descriptions'])
                    
                    # Add some randomness to amounts
                    amount = amount * random.uniform(0.8, 1.2)
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        sender=random.choice(users),
                        receiver=f"TEST - {description}",
                        department=random.choice(departments),
                        category=category,
                        subcategory=subcategory,
                        type=random.choice(['Other', 'Management', 'Health', 'Transport']),
                        transaction_date=current_date,
                        amount=Decimal(str(round(amount, 2))),
                        qty=Decimal(str(random.uniform(1, 5))),
                        description=f"TEST - {description}",
                        payment_method=random.choice(['Cash', 'Mpesa', 'Check', 'Other']),
                    )
                    transactions.append(transaction)
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'Created {len(transactions)} historical transactions')
        return transactions

    def create_sample_budgets(self, companies, departments, categories, users):
        """Create sample budgets with different types and timeframes"""
        budgets = []
        
        # Get subcategories
        operations_cat = categories[0]  # Operations
        tech_cat = categories[1]  # Technology
        marketing_cat = categories[2]  # Marketing
        dev_cat = categories[3]  # Development
        
        # General monthly budgets
        general_budgets = [
            {
                'item_name': 'Monthly Office Supplies',
                'description': 'TEST - Monthly office supplies budget',
                'budget_type': 'general',
                'timeframe': 'monthly',
                'category': operations_cat,
                'subcategory': operations_cat.subcategories.filter(name='Office Supplies').first(),
                'quantity': 1,
                'unit_price': 500,
                'estimation_method': 'transaction_based',
                'status': 'active',
            },
            {
                'item_name': 'Monthly Utilities',
                'description': 'TEST - Monthly utilities budget',
                'budget_type': 'general',
                'timeframe': 'monthly',
                'category': operations_cat,
                'subcategory': operations_cat.subcategories.filter(name='Utilities').first(),
                'quantity': 1,
                'unit_price': 1200,
                'estimation_method': 'transaction_based',
                'status': 'active',
            },
        ]
        
        # Website development budgets
        web_budgets = [
            {
                'item_name': 'E-commerce Website Development',
                'description': 'TEST - Full e-commerce website development project',
                'budget_type': 'website_development',
                'timeframe': 'monthly',
                'project_name': 'E-commerce Platform',
                'project_description': 'Complete e-commerce website with payment integration',
                'category': dev_cat,
                'subcategory': dev_cat.subcategories.filter(name='Development Tools').first(),
                'quantity': 1,
                'unit_price': 15000,
                'estimation_method': 'coda_estimation',
                'status': 'submitted',
            },
            {
                'item_name': 'Corporate Website Redesign',
                'description': 'TEST - Corporate website redesign project',
                'budget_type': 'website_development',
                'timeframe': 'monthly',
                'project_name': 'Corporate Website',
                'project_description': 'Modern corporate website with CMS',
                'category': dev_cat,
                'subcategory': dev_cat.subcategories.filter(name='Third-party Services').first(),
                'quantity': 1,
                'unit_price': 8000,
                'estimation_method': 'coda_estimation',
                'status': 'approved',
            },
        ]
        
        # Investment budgets
        investment_budgets = [
            {
                'item_name': 'New Development Equipment',
                'description': 'TEST - Purchase of new development workstations',
                'budget_type': 'investment',
                'timeframe': 'yearly',
                'category': tech_cat,
                'subcategory': tech_cat.subcategories.filter(name='Hardware').first(),
                'quantity': 5,
                'unit_price': 2000,
                'estimation_method': 'manual',
                'status': 'draft',
                'is_investment': True,
                'investment_type': 'equipment',
                'expected_roi': 25.0,
                'payback_period': 18,
            },
            {
                'item_name': 'Marketing Software License',
                'description': 'TEST - Annual marketing automation software license',
                'budget_type': 'investment',
                'timeframe': 'yearly',
                'category': marketing_cat,
                'subcategory': marketing_cat.subcategories.filter(name='Digital Marketing').first(),
                'quantity': 1,
                'unit_price': 5000,
                'estimation_method': 'manual',
                'status': 'draft',
                'is_investment': True,
                'investment_type': 'software',
                'expected_roi': 40.0,
                'payback_period': 12,
            },
        ]
        
        # Operations budgets
        operations_budgets = [
            {
                'item_name': 'Monthly Operations',
                'description': 'TEST - Monthly operations budget',
                'budget_type': 'operations',
                'timeframe': 'monthly',
                'category': operations_cat,
                'subcategory': operations_cat.subcategories.filter(name='Office Supplies').first(),
                'quantity': 1,
                'unit_price': 2000,
                'estimation_method': 'transaction_based',
                'status': 'active',
            },
        ]
        
        # Marketing budgets
        marketing_budgets = [
            {
                'item_name': 'Q1 Marketing Campaign',
                'description': 'TEST - Q1 marketing campaign budget',
                'budget_type': 'marketing',
                'timeframe': 'quarterly',
                'category': marketing_cat,
                'subcategory': marketing_cat.subcategories.filter(name='Digital Marketing').first(),
                'quantity': 1,
                'unit_price': 10000,
                'estimation_method': 'trend_analysis',
                'status': 'active',
            },
        ]
        
        # Combine all budget types
        all_budgets = general_budgets + web_budgets + investment_budgets + operations_budgets + marketing_budgets
        
        # Create budgets
        for budget_data in all_budgets:
            budget = Budget.objects.create(
                company=companies[0],  # CODA
                department=random.choice(departments),
                budget_lead=random.choice(users),
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=30),
                **budget_data
            )
            budgets.append(budget)
        
        self.stdout.write(f'Created {len(budgets)} sample budgets')
        return budgets

    def create_estimation_templates(self):
        """Create budget estimation templates"""
        templates = []
        
        # CODA Development Template
        coda_template = BudgetEstimationTemplate.objects.create(
            name='CODA Development Template',
            description='Standard CODA development cost estimation template',
            budget_type='website_development',
            estimation_config={
                'base_cost': 1000,
                'cost_per_model': 500,
                'cost_per_view': 200,
                'cost_per_template': 100,
                'cost_per_api': 300,
            },
            development_tasks={
                'createview': {'hour': 10, 'quantity': 1, 'unit_price': 30},
                'updateview': {'hour': 5, 'quantity': 1, 'unit_price': 30},
                'listview': {'hour': 3, 'quantity': 1, 'unit_price': 30},
                'detailview': {'hour': 3, 'quantity': 1, 'unit_price': 30},
                'deleteview': {'hour': 2, 'quantity': 1, 'unit_price': 30},
                'template': {'hour': 5, 'quantity': 3, 'unit_price': 30},
                'form': {'hour': 4, 'quantity': 1, 'unit_price': 30},
                'api': {'hour': 10, 'quantity': 3, 'unit_price': 30},
            },
            hourly_rate=30.00
        )
        templates.append(coda_template)
        
        # Marketing Template
        marketing_template = BudgetEstimationTemplate.objects.create(
            name='Marketing Campaign Template',
            description='Standard marketing campaign cost estimation',
            budget_type='marketing',
            estimation_config={
                'base_cost': 1000,
                'cost_per_lead': 50,
                'cost_per_conversion': 200,
                'platform_costs': {
                    'google_ads': 0.3,
                    'facebook_ads': 0.2,
                    'linkedin_ads': 0.1,
                    'other': 0.4
                }
            },
            hourly_rate=25.00
        )
        templates.append(marketing_template)
        
        # Operations Template
        operations_template = BudgetEstimationTemplate.objects.create(
            name='Operations Template',
            description='Standard operations cost estimation',
            budget_type='operations',
            estimation_config={
                'office_supplies_per_employee': 100,
                'utilities_per_sqft': 2.5,
                'rent_per_sqft': 15,
                'insurance_rate': 0.02
            },
            hourly_rate=20.00
        )
        templates.append(operations_template)
        
        self.stdout.write(f'Created {len(templates)} estimation templates')
        return templates

    def create_multi_year_plans(self, companies, departments, users):
        """Create multi-year budget plans"""
        plans = []
        
        # 5-Year Strategic Plan
        plan_5yr = MultiYearBudgetPlan.objects.create(
            name='CODA 5-Year Strategic Plan',
            description='TEST - Comprehensive 5-year strategic plan for CODA',
            company=companies[0],  # CODA
            department=departments[0],  # Development
            created_by=users[0],  # Admin
            start_year=2024,
            end_year=2028,
            plan_type='5_year',
            total_investment_required=500000,
            funding_sources=[
                {'source': 'Internal Cash Flow', 'amount': 150000, 'percentage': 30},
                {'source': 'Long-term Loan', 'amount': 250000, 'percentage': 50},
                {'source': 'Investment/Equity', 'amount': 100000, 'percentage': 20},
            ],
            status='approved'
        )
        plans.append(plan_5yr)
        
        # 2-Year Growth Plan
        plan_2yr = MultiYearBudgetPlan.objects.create(
            name='CODA 2-Year Growth Plan',
            description='TEST - 2-year growth and expansion plan',
            company=companies[0],  # CODA
            department=departments[1],  # Marketing
            created_by=users[1],  # Finance Manager
            start_year=2024,
            end_year=2025,
            plan_type='2_year',
            total_investment_required=200000,
            funding_sources=[
                {'source': 'Internal Cash Flow', 'amount': 100000, 'percentage': 50},
                {'source': 'Short-term Loan', 'amount': 100000, 'percentage': 50},
            ],
            status='active'
        )
        plans.append(plan_2yr)
        
        # 1-Year Operational Plan
        plan_1yr = MultiYearBudgetPlan.objects.create(
            name='CODA 1-Year Operational Plan',
            description='TEST - 1-year operational efficiency plan',
            company=companies[0],  # CODA
            department=departments[2],  # Operations
            created_by=users[2],  # Dev Lead
            start_year=2024,
            end_year=2024,
            plan_type='1_year',
            total_investment_required=50000,
            funding_sources=[
                {'source': 'Internal Cash Flow', 'amount': 50000, 'percentage': 100},
            ],
            status='draft'
        )
        plans.append(plan_1yr)
        
        self.stdout.write(f'Created {len(plans)} multi-year budget plans')
        return plans

    def create_approval_policies(self):
        """Create realistic approval policies"""
        policies = []
        
        # Small Expense Policy
        small_policy = ApprovalPolicy.objects.create(
            name='Small Expense Approval Policy',
            description='Policy for small operational expenses under $1,000 requiring manager approval and OTP verification',
            min_amount=100,
            max_amount=1000,
            approver_roles=['manager'],
            approval_chain='manager',
            auto_approve=False,
            requires_otp=True,
            applicable_user_types=['staff'],
            max_approval_days=3,
            escalation_days=1
        )
        policies.append(small_policy)
        
        # Medium Expense Policy
        medium_policy = ApprovalPolicy.objects.create(
            name='Medium Expense Approval Policy',
            description='Policy for medium operational expenses between $1,000-$10,000 requiring department head and finance manager approval',
            min_amount=1000,
            max_amount=10000,
            approver_roles=['department_head', 'finance_manager'],
            approval_chain='department_head,finance_manager',
            auto_approve=False,
            requires_otp=True,
            applicable_user_types=['staff', 'manager'],
            max_approval_days=7,
            escalation_days=2
        )
        policies.append(medium_policy)
        
        # Large Expense Policy
        large_policy = ApprovalPolicy.objects.create(
            name='Large Expense Approval Policy',
            description='Policy for large expenses over $10,000 requiring executive approval and board notification',
            min_amount=10000,
            max_amount=100000,
            approver_roles=['ceo', 'cfo'],
            approval_chain='ceo,cfo',
            auto_approve=False,
            requires_otp=True,
            applicable_user_types=['manager', 'department_head'],
            max_approval_days=14,
            escalation_days=3
        )
        policies.append(large_policy)
        
        # Investment Policy
        investment_policy = ApprovalPolicy.objects.create(
            name='Investment Approval Policy',
            description='Policy for investment-related expenses requiring investment committee approval',
            min_amount=5000,
            max_amount=500000,
            approver_roles=['investment_committee', 'cfo'],
            approval_chain='investment_committee,cfo',
            auto_approve=False,
            requires_otp=True,
            applicable_user_types=['manager', 'department_head'],
            max_approval_days=21,
            escalation_days=5
        )
        policies.append(investment_policy)
        
        # Emergency Policy
        emergency_policy = ApprovalPolicy.objects.create(
            name='Emergency Expense Policy',
            description='Policy for emergency expenses with expedited approval process',
            min_amount=500,
            max_amount=5000,
            approver_roles=['manager', 'emergency_approver'],
            approval_chain='manager,emergency_approver',
            auto_approve=False,
            requires_otp=False,  # No OTP for emergencies
            applicable_user_types=['staff', 'manager'],
            max_approval_days=1,
            escalation_days=0
        )
        policies.append(emergency_policy)
        
        self.stdout.write(f'Created {len(policies)} approval policies')
        return policies
