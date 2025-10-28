"""
Management command to populate MeetingActivityMapping from hardcoded dictionary.

PHASE 3 IMPROVEMENT: Convert hardcoded activity_mapping dict to database records.

Usage:
    python manage.py populate_meeting_mappings
"""

from django.core.management.base import BaseCommand
from ai_services.models import MeetingActivityMapping
from ai_services.utils import activity_mapping


class Command(BaseCommand):
    help = 'Populate MeetingActivityMapping table from hardcoded activity_mapping dict'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🚀 Populating Meeting Activity Mappings...\n'))
        
        created_count = 0
        updated_count = 0
        
        for meeting_id, activity_name in activity_mapping.items():
            mapping, created = MeetingActivityMapping.objects.update_or_create(
                meeting_id_pattern=meeting_id,
                defaults={
                    'activity_name': activity_name,
                    'task_points': 1,  # Default: 1 point per attendance
                    'min_duration_minutes': 3,
                    'is_active': True,
                    'description': f'Auto-migrated from hardcoded mapping'
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Created: {meeting_id} → {activity_name}')
            else:
                updated_count += 1
                self.stdout.write(f'  ⏭️  Updated: {meeting_id} → {activity_name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Complete!'))
        self.stdout.write(f'   Created: {created_count}')
        self.stdout.write(f'   Updated: {updated_count}')
        self.stdout.write(f'   Total: {MeetingActivityMapping.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n✅ Activity mappings populated successfully!\n'))

