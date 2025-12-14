#!/usr/bin/env python
"""
Setup script for email verification
Initializes the Site object required by django-allauth
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings


def setup_site():
    """Create or update the Site object for email verification"""
    print("Setting up Site object for email verification...")

    try:
        site = Site.objects.get(id=settings.SITE_ID)
        print(f"✓ Site object already exists: {site.domain}")

        # Update site information
        if settings.DEBUG:
            site.domain = 'localhost:8000'
            site.name = 'Biashara Bridges (Development)'
        else:
            # Update this for production
            site.domain = 'biasharabridges.com'
            site.name = 'Biashara Bridges'

        site.save()
        print(f"✓ Updated site: {site.domain}")

    except Site.DoesNotExist:
        print("✗ Site object does not exist. Creating...")

        if settings.DEBUG:
            domain = 'localhost:8000'
            name = 'Biashara Bridges (Development)'
        else:
            domain = 'biasharabridges.com'
            name = 'Biashara Bridges'

        site = Site.objects.create(
            id=settings.SITE_ID,
            domain=domain,
            name=name
        )
        print(f"✓ Created site: {site.domain}")

    print("\n✓ Email verification setup complete!")
    print(f"  - Site ID: {site.id}")
    print(f"  - Domain: {site.domain}")
    print(f"  - Name: {site.name}")
    print(f"\nVerification emails will use links like:")
    print(f"  http{'s' if not settings.DEBUG else ''}://{site.domain}/accounts/confirm-email/<key>/")


if __name__ == '__main__':
    setup_site()
