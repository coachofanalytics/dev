#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Category

# Define categories for a business networking platform
categories_data = [
    {
        'name': 'Technology',
        'slug': 'technology',
        'description': 'Software, IT services, and tech solutions',
        'icon': 'bi-laptop'
    },
    {
        'name': 'Finance',
        'slug': 'finance',
        'description': 'Banking, investment, and financial services',
        'icon': 'bi-cash-coin'
    },
    {
        'name': 'Agriculture',
        'slug': 'agriculture',
        'description': 'Farming, agribusiness, and food production',
        'icon': 'bi-tree'
    },
    {
        'name': 'Manufacturing',
        'slug': 'manufacturing',
        'description': 'Production, assembly, and industrial services',
        'icon': 'bi-gear'
    },
    {
        'name': 'Retail',
        'slug': 'retail',
        'description': 'Shops, stores, and e-commerce',
        'icon': 'bi-shop'
    },
    {
        'name': 'Healthcare',
        'slug': 'healthcare',
        'description': 'Medical services, clinics, and health products',
        'icon': 'bi-heart-pulse'
    },
    {
        'name': 'Education',
        'slug': 'education',
        'description': 'Schools, training, and educational services',
        'icon': 'bi-book'
    },
    {
        'name': 'Real Estate',
        'slug': 'real-estate',
        'description': 'Property, construction, and housing',
        'icon': 'bi-house'
    },
    {
        'name': 'Transportation',
        'slug': 'transportation',
        'description': 'Logistics, delivery, and transport services',
        'icon': 'bi-truck'
    },
    {
        'name': 'Hospitality',
        'slug': 'hospitality',
        'description': 'Hotels, restaurants, and tourism',
        'icon': 'bi-cup-hot'
    },
    {
        'name': 'Professional Services',
        'slug': 'professional-services',
        'description': 'Consulting, legal, and business services',
        'icon': 'bi-briefcase'
    },
    {
        'name': 'Arts & Media',
        'slug': 'arts-media',
        'description': 'Creative industries, media, and entertainment',
        'icon': 'bi-palette'
    }
]

# Create categories
created_count = 0
updated_count = 0

for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults={
            'name': cat_data['name'],
            'description': cat_data['description'],
            'icon': cat_data['icon'],
            'is_active': True
        }
    )

    if created:
        created_count += 1
        print(f'✓ Created category: {category.name}')
    else:
        # Update existing category
        category.name = cat_data['name']
        category.description = cat_data['description']
        category.icon = cat_data['icon']
        category.is_active = True
        category.save()
        updated_count += 1
        print(f'↻ Updated category: {category.name}')

print(f'\nSummary: {created_count} created, {updated_count} updated')
print(f'Total categories in database: {Category.objects.count()}')
