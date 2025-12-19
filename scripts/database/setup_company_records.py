#!/usr/bin/env python3
"""
Setup Company Records for Multi-Organization Receipt Branding

This script creates/updates Company records for CODA, DC48K, and Biashara Bridges
with their respective branding information.

Usage:
    python scripts/setup_company_records.py
    # Or with Django settings:
    python manage.py shell < scripts/setup_company_records.py
"""

import os
import sys
import django

# Setup Django
if __name__ == "__main__":
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.coda_settings.local_settings')
    django.setup()

from main.models import Company


def setup_companies():
    """Create or update Company records for multi-organization receipt branding"""
    
    companies_data = [
        {
            'slug': 'coda',
            'name': 'CODA Analytics',
            'display_name': 'CODA ANALYTICS',
            'website': 'www.codanalytics.net',
            'receipt_email': 'info@codanalytics.net',
            'sector': 'Technology & Training',
            'mission': 'Professional Training & Development',
            'address': None,  # Add address if needed
        },
        {
            'slug': 'dc48k',
            'name': 'Diaspora County 48K',
            'display_name': 'DC48K',
            'website': 'www.diasporacounty48.org',
            'receipt_email': 'info@diasporacounty48.org',
            'sector': 'Community Development',
            'mission': 'Diaspora Community Development',
            'address': None,
        },
        {
            'slug': 'biashara',
            'name': 'Biashara Bridges',
            'display_name': 'Biashara Bridges',
            'website': 'www.biasharabridges.com',
            'receipt_email': 'info@biasharabridges.com',
            'sector': 'Business Development',
            'mission': 'Connecting Businesses Across Borders',
            'address': None,
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    print("🏢 Setting up Company records for multi-organization receipt branding...")
    print("=" * 70)
    
    for company_data in companies_data:
        slug = company_data.pop('slug')
        
        # Get or create company
        company, created = Company.objects.get_or_create(
            slug=slug,
            defaults=company_data
        )
        
        if created:
            print(f"✅ Created: {company.name} ({slug})")
            created_count += 1
        else:
            # Update existing company with new branding fields
            for key, value in company_data.items():
                if value:  # Only update if value is provided
                    setattr(company, key, value)
            company.save()
            print(f"🔄 Updated: {company.name} ({slug})")
            updated_count += 1
        
        # Display company info
        print(f"   Website: {company.website}")
        print(f"   Receipt Email: {company.receipt_email}")
        print(f"   Display Name: {company.display_name}")
        print()
    
    print("=" * 70)
    print(f"✅ Setup complete!")
    print(f"   Created: {created_count} companies")
    print(f"   Updated: {updated_count} companies")
    print()
    print("📋 Next steps:")
    print("   1. Upload logos to: coda/static/main/img/logos/")
    print("   2. Update logo field in Django Admin if needed")
    print("   3. Test payment flows from different domains")


if __name__ == "__main__":
    setup_companies()

