#!/usr/bin/env python
"""
Script to export/import reference data between environments.
Usage:
  Export: python sync_reference_data.py export
  Import: python sync_reference_data.py import reference_data.json
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core import serializers
from accounts.models import Category, Role

def export_reference_data():
    """Export categories and roles to JSON"""
    data = []

    # Export Categories
    categories = Category.objects.all()
    data.extend(serializers.serialize('json', categories, indent=2))

    # Export Roles
    roles = Role.objects.all()
    data.extend(serializers.serialize('json', roles, indent=2))

    filename = 'reference_data.json'
    with open(filename, 'w') as f:
        f.write('[')
        f.write(','.join(data))
        f.write(']')

    print(f'✓ Exported {categories.count()} categories and {roles.count()} roles to {filename}')
    return filename

def import_reference_data(filename):
    """Import categories and roles from JSON"""
    from django.core.management import call_command

    try:
        call_command('loaddata', filename)
        print(f'✓ Successfully imported data from {filename}')
    except Exception as e:
        print(f'✗ Error importing data: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  Export: python sync_reference_data.py export')
        print('  Import: python sync_reference_data.py import reference_data.json')
        sys.exit(1)

    command = sys.argv[1]

    if command == 'export':
        export_reference_data()
    elif command == 'import':
        if len(sys.argv) < 3:
            print('Error: Please specify the JSON file to import')
            sys.exit(1)
        import_reference_data(sys.argv[2])
    else:
        print(f'Unknown command: {command}')
        sys.exit(1)
