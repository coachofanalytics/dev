#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Category

# Define user type categories
user_types = [
    {
        'name': 'Individual',
        'slug': 'individual',
        'description': 'Individual professional or freelancer',
        'icon': 'bi-person'
    },
    {
        'name': 'Business',
        'slug': 'business',
        'description': 'Business or company',
        'icon': 'bi-building'
    },
    {
        'name': 'Investor',
        'slug': 'investor',
        'description': 'Investor looking for opportunities',
        'icon': 'bi-graph-up-arrow'
    }
]

# Create user type categories
created_count = 0
updated_count = 0

for user_type in user_types:
    category, created = Category.objects.get_or_create(
        slug=user_type['slug'],
        defaults={
            'name': user_type['name'],
            'description': user_type['description'],
            'icon': user_type['icon'],
            'is_active': True
        }
    )

    if created:
        created_count += 1
        print(f'✓ Created user type: {category.name}')
    else:
        # Update existing category
        category.name = user_type['name']
        category.description = user_type['description']
        category.icon = user_type['icon']
        category.is_active = True
        category.save()
        updated_count += 1
        print(f'↻ Updated user type: {category.name}')

print(f'\nSummary: {created_count} created, {updated_count} updated')
print(f'Total categories in database: {Category.objects.count()}')
