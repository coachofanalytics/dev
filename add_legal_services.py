#!/usr/bin/env python
"""
Script to add sample legal services to the database.
Run with: python manage.py shell < add_legal_services.py
"""

from main.models import LegalService

# Visa and Residency Services
LegalService.objects.create(
    title='Visa and Residency Services',
    category='visa',
    description='Secure your status abroad with expert guidance on visa applications, extensions, and residency permits. We provide up-to-date information and procedural support to simplify your journey.',
    image_url='https://placehold.co/600x450/e0f2f1/000000?text=Visa+Image',
    features=[
        'Work Permit and Student Visa Assistance',
        'Family and Spousal Sponsorship Guidance',
        'Permanent Residency Application Support',
        'Visa Renewal and Extension Processing'
    ],
    cta_button_text='Start Your Application',
    cta_button_url='/services/visa-application',
    order=1,
    is_active=True
)

# Citizenship and Naturalization
LegalService.objects.create(
    title='Citizenship and Naturalization',
    category='citizenship',
    description='Achieve your goal of citizenship with our comprehensive support. We help you understand eligibility requirements, prepare documentation, and navigate the entire naturalization process.',
    image_url='https://placehold.co/600x450/fff7e6/000000?text=Citizenship+Image',
    features=[
        'Eligibility Assessment and Consultation',
        'Application and Documentation Review',
        'Guidance on Dual Citizenship Policies',
        'Preparation for Citizenship Tests and Interviews'
    ],
    cta_button_text='Explore Citizenship Paths',
    cta_button_url='/services/citizenship',
    order=2,
    is_active=True
)

# Legal Representation & Referrals
LegalService.objects.create(
    title='Legal Representation & Referrals',
    category='legal_referral',
    description='When you need direct legal counsel, we connect you to our network of vetted, experienced immigration and international law attorneys.',
    image_url='https://placehold.co/600x450/e0f2f1/000000?text=Legal+Referral+Image',
    features=[
        'Access to Vetted Immigration Lawyers',
        'Specialists in International Family Law',
        'Experts in Property and Business Law Abroad',
        'Support for Appeals and Litigation'
    ],
    cta_button_text='Find an Attorney',
    cta_button_url='/legal-referrals',
    order=3,
    is_active=True
)

print(f"✅ Created {LegalService.objects.count()} legal services successfully!")
