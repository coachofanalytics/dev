#!/usr/bin/env python3
"""
Create Investor Test User for CODA Investing App Testing
Run with: python3 manage.py shell < scripts/create_investor_test_user.py
"""

from accounts.models import CustomerUser
from accounts.choices import UserCategory
from investing.models import Investment_rates, Investor_Information
from decimal import Decimal
from datetime import date, timedelta

print("=" * 60)
print("🚀 CODA Investing App - Create Investor Test User")
print("=" * 60)

# Create or get investor user
username = 'investor_test'
email = 'investor@codaplatform.com'
password = 'Test@1234'

try:
    investor = CustomerUser.objects.get(username=username)
    print(f"\n✅ Investor user already exists: {investor.username}")
except CustomerUser.DoesNotExist:
    investor = CustomerUser.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name='John',
        last_name='Investor',
        category=UserCategory.INVESTOR,
        is_active=True,
        is_staff=False,
        is_superuser=False
    )
    print(f"\n✅ Created new investor user: {investor.username}")

print(f"\n📋 USER CREDENTIALS")
print("-" * 60)
print(f"Username: {username}")
print(f"Password: {password}")
print(f"Email: {email}")
print(f"Category: {investor.get_category_display()}")
print(f"Active: {investor.is_active}")

# Create sample investment plans if they don't exist
print(f"\n📊 INVESTMENT PLANS")
print("-" * 60)

plans_data = [
    {
        'name': 'Tier 1 Growth Plan',
        'type': 'investment',
        'tier': 'Tier 1',
        'base_amount': 1000,
        'duration': 12,
        'rate': Decimal('8.00'),
        'description': 'Entry-level growth investment plan for new investors',
        'advantages': 'Low minimum investment, competitive returns, quarterly updates',
    },
    {
        'name': 'Tier 2 Premium Plan',
        'type': 'investment',
        'tier': 'Tier 2',
        'base_amount': 5000,
        'duration': 18,
        'rate': Decimal('10.00'),
        'description': 'Premium investment plan with enhanced returns',
        'advantages': 'Higher returns, monthly reports, dedicated support',
    },
    {
        'name': 'Tier 3 Elite Plan',
        'type': 'investment',
        'tier': 'Tier 3',
        'base_amount': 25000,
        'duration': 24,
        'rate': Decimal('12.00'),
        'description': 'Elite investment plan for serious investors',
        'advantages': 'Maximum returns, weekly updates, priority support, exclusive benefits',
    },
]

for plan_data in plans_data:
    plan, created = Investment_rates.objects.get_or_create(
        name=plan_data['name'],
        defaults=plan_data
    )
    status = "✅ Created" if created else "ℹ️  Already exists"
    print(f"{status}: {plan.name} - {plan.rate}% ({plan.tier})")

# Create sample investment for testing
print(f"\n💼 SAMPLE INVESTMENT")
print("-" * 60)

sample_investment_data = {
    'investor': investor,
    'amount_invested': Decimal('5000.00'),
    'investment_type': 'equity',
    'investment_date': date.today() - timedelta(days=30),
    'duration': 12,
    'expected_return_rate': Decimal('8.00'),
    'actual_return_rate': Decimal('5.50'),
    'current_value': Decimal('5225.00'),
    'total_returns_paid': Decimal('225.00'),
    'investment_purpose': 'Long-term growth and portfolio diversification',
    'model_type': 'Installment',
    'status': 'active',
    'risk_tolerance': 'moderate',
    'kyc_status': 'verified',
    'quarterly_updates': True,
    'monthly_reports': True,
}

try:
    sample_investment = Investor_Information.objects.filter(
        investor=investor
    ).first()
    
    if sample_investment:
        print(f"ℹ️  Sample investment already exists: ID {sample_investment.id}")
    else:
        sample_investment = Investor_Information.objects.create(**sample_investment_data)
        print(f"✅ Created sample investment: ID {sample_investment.id}")
    
    print(f"   Amount: ${sample_investment.amount_invested}")
    print(f"   Current Value: ${sample_investment.current_value}")
    print(f"   Returns: ${sample_investment.total_returns_paid}")
    print(f"   Status: {sample_investment.status}")
    
except Exception as e:
    print(f"⚠️  Could not create sample investment: {str(e)}")

# Testing URLs
print(f"\n🔗 TESTING URLS")
print("-" * 60)
print("Login URL: http://localhost:8000/accounts/login/")
print("Investing Home: http://localhost:8000/investing/")
print("Dashboard: http://localhost:8000/investing/dashboard/")
print("Individual Investments: http://localhost:8000/investing/individual-investments/")
print("Risk Dashboard: http://localhost:8000/investing/risk/risk-dashboard/")
print("Portfolio: http://localhost:8000/investing/myportfolio/")
print("Apply for Investment: http://localhost:8000/investing/apply/")

print(f"\n🎯 TESTING INSTRUCTIONS")
print("-" * 60)
print("1. Navigate to: http://localhost:8000/accounts/login/")
print(f"2. Login with:")
print(f"   Username: {username}")
print(f"   Password: {password}")
print("3. Follow the test plan in:")
print("   docs/apps/investing/USER_FLOW_TEST/INVESTOR_USER_FLOW_TEST.md")

print(f"\n" + "=" * 60)
print("✅ Setup Complete! Ready for testing.")
print("=" * 60)

