import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile, Category
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity
from decimal import Decimal
from datetime import date, timedelta

business_category, _ = Category.objects.get_or_create(
    slug="business",
    defaults={"name": "Business", "description": "Business users", "is_active": True}
)

businesses_data = [
    {"username": "techstartup", "email": "tech@startup.com", "company": "TechVenture Inc",
     "industry": "Technology", "stage": "seed", "size": "1-10", "seeking": 500000, "equity": 15, "revenue": 100000},
    {"username": "greeneco", "email": "info@greeneco.com", "company": "GreenEco Solutions",
     "industry": "Renewable Energy", "stage": "series_a", "size": "11-50", "seeking": 2000000, "equity": 20, "revenue": 500000},
    {"username": "fooddelivery", "email": "hello@fooddelivery.com", "company": "QuickBite Delivery",
     "industry": "Food & Beverage", "stage": "series_b", "size": "51-200", "seeking": 5000000, "equity": 10, "revenue": 2000000},
]

created_businesses = []

for biz_data in businesses_data:
    user, created = User.objects.get_or_create(
        username=biz_data["username"],
        defaults={"email": biz_data["email"], "first_name": biz_data["company"].split()[0], "last_name": "Team"}
    )
    if created:
        user.set_password("testpass123")
        user.save()
        print(f"Created user: {user.username}")

    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"category": business_category})

    business_profile, created = BusinessProfile.objects.get_or_create(
        user=user,
        defaults={
            "company_name": biz_data["company"], "industry": biz_data["industry"],
            "company_size": biz_data["size"], "funding_stage": biz_data["stage"],
            "investment_seeking": Decimal(str(biz_data["seeking"])), "equity_offered": Decimal(str(biz_data["equity"])),
            "annual_revenue": Decimal(str(biz_data["revenue"])), "founded_date": date(2020, 1, 1)
        }
    )
    if created:
        print(f"Created BusinessProfile: {business_profile.company_name}")

    created_businesses.append((user, business_profile))

opportunities_data = [
    {"business_idx": 0, "title": "Seed Funding for AI Analytics Platform",
     "description": "Building AI-powered analytics platform for businesses.",
     "amount": 500000, "min_investment": 25000, "equity": 15, "type": "equity", "industry": "Technology"},
    {"business_idx": 1, "title": "Solar Energy Expansion Investment",
     "description": "Revolutionizing renewable energy access in East Africa.",
     "amount": 2000000, "min_investment": 100000, "equity": 20, "type": "equity", "industry": "Renewable Energy"},
]

for opp_data in opportunities_data:
    user, biz_profile = created_businesses[opp_data["business_idx"]]
    opp, created = InvestmentOpportunity.objects.get_or_create(
        business=user, title=opp_data["title"],
        defaults={
            "description": opp_data["description"], "amount_seeking": Decimal(str(opp_data["amount"])),
            "minimum_investment": Decimal(str(opp_data["min_investment"])), "equity_percentage": Decimal(str(opp_data["equity"])),
            "investment_type": opp_data["type"], "industry": opp_data["industry"], "stage": biz_profile.funding_stage,
            "status": "open", "deadline": date.today() + timedelta(days=90)
        }
    )
    if created:
        print(f"Created Opportunity: {opp.title}")

jobs_data = [
    {"business_idx": 0, "title": "Senior Full Stack Developer",
     "description": "Join our tech startup as Senior Full Stack Developer.",
     "requirements": "Python, React, 5+ years experience",
     "responsibilities": "Lead development team, architect solutions",
     "type": "full_time", "level": "senior", "location": "Nairobi, Kenya", "remote": True,
     "salary_min": 80000, "salary_max": 120000},
    {"business_idx": 1, "title": "Solar Energy Engineer",
     "description": "Experienced Solar Energy Engineer needed.",
     "requirements": "Engineering degree, 3+ years solar experience",
     "responsibilities": "Design solar systems, manage installations",
     "type": "full_time", "level": "mid", "location": "Kigali, Rwanda", "remote": False,
     "salary_min": 50000, "salary_max": 70000},
]

for job_data in jobs_data:
    user, _ = created_businesses[job_data["business_idx"]]
    job, created = JobOpportunity.objects.get_or_create(
        business=user, title=job_data["title"],
        defaults={
            "description": job_data["description"], "requirements": job_data["requirements"],
            "responsibilities": job_data["responsibilities"], "job_type": job_data["type"],
            "experience_level": job_data["level"], "location": job_data["location"],
            "remote_option": job_data["remote"], "salary_min": Decimal(str(job_data["salary_min"])),
            "salary_max": Decimal(str(job_data["salary_max"])), "salary_currency": "USD",
            "status": "open", "deadline": date.today() + timedelta(days=60)
        }
    )
    if created:
        print(f"Created Job: {job.title}")

print("\n=== Sample Data Created! ===")
print(f"Businesses: {BusinessProfile.objects.count()}")
print(f"Opportunities: {InvestmentOpportunity.objects.count()}")
print(f"Jobs: {JobOpportunity.objects.count()}")
