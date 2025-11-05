"""
Management command to create Django Groups for team categories.

Usage:
    python manage.py create_team_groups
    python manage.py create_team_groups --recreate
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create Django Groups for team categories'
    
    TEAM_GROUPS = [
        'BOG/Leadership',
        'Elite Team',
        'Lead Team',
        'Support Team',
        'Senior Analysts',
        'Junior Analysts',
        'Senior Trainee',
        'Junior Trainee',
        'Elementary',
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Delete and recreate all groups',
        )
    
    def handle(self, *args, **options):
        recreate = options['recreate']
        
        self.stdout.write(self.style.SUCCESS('\n🏗️ Creating Team Groups\n'))
        self.stdout.write('=' * 70 + '\n')
        
        if recreate:
            self.stdout.write(self.style.WARNING('Recreate mode: Deleting existing groups...\n'))
            deleted_count = Group.objects.filter(name__in=self.TEAM_GROUPS).delete()[0]
            self.stdout.write(f'Deleted {deleted_count} existing groups\n')
        
        created_count = 0
        existing_count = 0
        
        for group_name in self.TEAM_GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Created: {group_name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    f'  ⏭️  Already exists: {group_name}'
                )
        
        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('\n📊 SUMMARY:')
        self.stdout.write(f'  ✅ Created: {created_count}')
        self.stdout.write(f'  ⏭️  Already existed: {existing_count}')
        self.stdout.write(f'  📂 Total groups: {len(self.TEAM_GROUPS)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Team groups ready!'
            )
        )
        
        # Show all groups
        self.stdout.write('\n📂 All Team Groups:')
        for i, group_name in enumerate(self.TEAM_GROUPS, 1):
            member_count = Group.objects.get(name=group_name).user_set.count()
            self.stdout.write(
                f'  {i}. {group_name:25} ({member_count} members)'
            )
        
        self.stdout.write(
            '\nNext steps:\n'
            '  1. python manage.py verify_team_members\n'
            '  2. python manage.py assign_manual_team_members\n'
        )

