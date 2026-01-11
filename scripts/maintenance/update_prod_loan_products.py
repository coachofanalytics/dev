#!/usr/bin/env python
"""
Script to update loan product types in production database.
Run this after confirming you're connected to production.

Usage:
    python update_prod_loan_products.py
    OR
    python manage.py shell < update_prod_loan_products.py
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coda_project.settings")
django.setup()

from django.db.models import Count, Q
from finance.models import LoanProduct

print("=" * 70)
print("UPDATING LOAN PRODUCT TYPES IN PRODUCTION")
print("=" * 70)

# Show current state
print("\n📊 Products BEFORE Update:")
for product in LoanProduct.objects.all().order_by("name"):
    print(
        f"   {product.name:40} | Type: {product.product_type:20} | Active: {product.is_active}"
    )

updated_count = 0
updated_products = []

for product in LoanProduct.objects.all():
    name_lower = product.name.lower()
    old_type = product.product_type
    new_type = None

    # Determine new type based on name
    if "kcc" in name_lower:
        new_type = "kcc_premium"
    elif "staff emergency" in name_lower or (
        "staff" in name_lower and "emergency" in name_lower
    ):
        new_type = "staff_emergency"
    elif "staff development" in name_lower or (
        "staff" in name_lower and "development" in name_lower
    ):
        new_type = "staff_development"
    elif "education" in name_lower:
        new_type = "education"
    elif "home improvement" in name_lower:
        new_type = "home_improvement"
    elif "medical" in name_lower:
        new_type = "medical_emergency"
    elif "vehicle" in name_lower:
        new_type = "vehicle_purchase"
    elif "debt" in name_lower:
        new_type = "debt_consolidation"
    elif "wedding" in name_lower or "event" in name_lower:
        new_type = "wedding_events"
    elif "business" in name_lower or "startup" in name_lower:
        new_type = "business_startup"
    else:
        new_type = "general"  # Keep as general for test products or unknown

    if new_type and new_type != old_type:
        print(f"\n📝 Updating: {product.name}")
        print(f"   Old: {old_type} → New: {new_type}")
        product.product_type = new_type
        product.save()
        updated_count += 1
        updated_products.append((product.name, old_type, new_type))
    else:
        print(f"\n✓ Keeping: {product.name} ({product.product_type})")

print(f"\n" + "=" * 70)
print(f"✅ Updated {updated_count} products")
print("=" * 70)

# Verify updates
print(f"\n📊 Verification - Product Type Distribution:")
type_counts = (
    LoanProduct.objects.values("product_type")
    .annotate(total=Count("id"), active=Count("id", filter=Q(is_active=True)))
    .order_by("product_type")
)
for item in type_counts:
    print(
        f'  - {item["product_type"]:25} : {item["total"]:2} total, {item["active"]:2} active'
    )

if updated_products:
    print(f"\n📝 Updated Products Summary:")
    for name, old, new in updated_products:
        print(f"   {name:40} : {old:20} → {new}")

print("\n✅ Update complete!")
