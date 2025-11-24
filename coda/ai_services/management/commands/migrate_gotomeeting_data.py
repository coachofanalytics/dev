"""
Management command to migrate legacy GotoMeetings data to normalized models.

This script migrates 48 existing meetings from the denormalized GotoMeetings model
to the new normalized Meeting + MeetingAttendee structure.

Usage:
    python manage.py migrate_gotomeeting_data [--dry-run]

The --dry-run flag will show what would be migrated without actually making changes.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from ai_services.models import GotoMeetings, Meeting, MeetingAttendee
from shared_core.users import CustomerUser
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate legacy GotoMeetings data to normalized Meeting + MeetingAttendee models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        # Get all legacy meetings
        old_meetings = GotoMeetings.objects.all()
        total_old_records = old_meetings.count()
        
        self.stdout.write(f'\n📊 Found {total_old_records} legacy GoToMeeting records')
        
        # Group by meeting_id to find unique meetings
        meeting_ids = old_meetings.values_list('meeting_id', flat=True).distinct()
        unique_meeting_count = len(meeting_ids)
        
        self.stdout.write(f'📊 Found {unique_meeting_count} unique meetings')
        self.stdout.write(f'📊 Average {total_old_records / unique_meeting_count:.1f} attendees per meeting\n')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run - showing what would be migrated:\n'))
            self._dry_run_preview(old_meetings, meeting_ids)
            return
        
        # Actual migration
        self._migrate_data(old_meetings, meeting_ids)

    def _dry_run_preview(self, old_meetings, meeting_ids):
        """Show preview of what would be migrated"""
        for i, meeting_id in enumerate(meeting_ids[:5], 1):  # Show first 5
            records = old_meetings.filter(meeting_id=meeting_id)
            first_record = records.first()
            
            self.stdout.write(f'\n{i}. Meeting: {first_record.meeting_topic or "Untitled"}')
            self.stdout.write(f'   ID: {meeting_id}')
            self.stdout.write(f'   Start: {first_record.meeting_start_time}')
            self.stdout.write(f'   Attendees: {records.count()}')
            
            for record in records:
                self.stdout.write(f'      - {record.attendee_name} ({record.attendee_email})')
        
        if len(meeting_ids) > 5:
            self.stdout.write(f'\n... and {len(meeting_ids) - 5} more meetings')

    @transaction.atomic
    def _migrate_data(self, old_meetings, meeting_ids):
        """Perform actual data migration"""
        self.stdout.write(self.style.SUCCESS('\n🚀 Starting migration...\n'))
        
        meetings_created = 0
        meetings_skipped = 0
        attendees_created = 0
        attendees_skipped = 0
        errors = 0
        
        for meeting_id in meeting_ids:
            try:
                # Get all records for this meeting
                records = old_meetings.filter(meeting_id=meeting_id)
                first_record = records.first()
                
                # Parse datetime
                start_time = self._parse_datetime_safe(first_record.meeting_start_time)
                end_time = self._parse_datetime_safe(first_record.meeting_end_time)
                
                if not start_time:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  Skipping meeting {meeting_id}: Invalid start_time'
                    ))
                    errors += 1
                    continue
                
                # Calculate duration
                if end_time and start_time:
                    duration_minutes = int((end_time - start_time).total_seconds() / 60)
                else:
                    duration_minutes = self._parse_duration_safe(first_record.meeting_duration)
                
                # Create or get Meeting
                meeting, created = Meeting.objects.get_or_create(
                    meeting_id=meeting_id,
                    defaults={
                        'topic': first_record.meeting_topic or 'Untitled Meeting',
                        'meeting_type': first_record.meeting_type or '',
                        'start_time': start_time,
                        'end_time': end_time or start_time,
                        'duration_minutes': duration_minutes,
                        'recording_url': first_record.recording or '',
                        'download_url': first_record.download_url or '',
                        'is_recorded': bool(first_record.recording),
                    }
                )
                
                if created:
                    meetings_created += 1
                    self.stdout.write(f'✅ Created meeting: {meeting.topic}')
                else:
                    meetings_skipped += 1
                    self.stdout.write(f'⏭️  Skipped existing meeting: {meeting.topic}')
                
                # Create MeetingAttendees
                for record in records:
                    if not record.attendee_email:
                        continue
                    
                    # Try to match to CODA user
                    user = self._find_user_by_email(record.attendee_email)
                    
                    # Parse attendee duration
                    attendee_duration = self._parse_duration_safe(record.attendee_duration)
                    
                    # Create or get MeetingAttendee
                    attendee, created = MeetingAttendee.objects.get_or_create(
                        meeting=meeting,
                        attendee_email=record.attendee_email,
                        defaults={
                            'user': user,
                            'attendee_name': record.attendee_name or record.attendee_email,
                            'duration_minutes': attendee_duration,
                            'is_organizer': False,
                            'task_points_awarded': False,
                        }
                    )
                    
                    if created:
                        attendees_created += 1
                    else:
                        attendees_skipped += 1
            
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(
                    f'❌ Error migrating meeting {meeting_id}: {str(e)}'
                ))
                logger.error(f'Migration error for meeting {meeting_id}: {e}', exc_info=True)
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎉 MIGRATION COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\n📊 Results:')
        self.stdout.write(f'   ✅ Meetings created: {meetings_created}')
        self.stdout.write(f'   ⏭️  Meetings skipped (already exist): {meetings_skipped}')
        self.stdout.write(f'   👥 Attendees created: {attendees_created}')
        self.stdout.write(f'   ⏭️  Attendees skipped (already exist): {attendees_skipped}')
        
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'   ❌ Errors: {errors}'))
        
        self.stdout.write('\n💡 Verification:')
        self.stdout.write(f'   Total meetings in new model: {Meeting.objects.count()}')
        self.stdout.write(f'   Total attendees in new model: {MeetingAttendee.objects.count()}')
        self.stdout.write(f'   Legacy records (unchanged): {GotoMeetings.objects.count()}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Migration successful!\n'))

    def _parse_datetime_safe(self, datetime_string):
        """Safely parse datetime string"""
        if not datetime_string:
            return None
        
        try:
            # Handle various datetime formats
            dt = parse_datetime(datetime_string)
            if dt:
                # Make timezone aware if naive
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                return dt
        except Exception as e:
            logger.warning(f'Could not parse datetime: {datetime_string} - {e}')
        
        return None

    def _parse_duration_safe(self, duration_string):
        """Safely parse duration string to minutes"""
        if not duration_string:
            return 0
        
        try:
            # Try to convert to int directly
            return int(duration_string)
        except (ValueError, TypeError):
            # Try to extract number from string
            import re
            numbers = re.findall(r'\d+', str(duration_string))
            if numbers:
                return int(numbers[0])
        
        return 0

    def _find_user_by_email(self, email):
        """Find CODA user by email"""
        if not email:
            return None
        
        try:
            return CustomerUser.objects.filter(email__iexact=email).first()
        except Exception:
            return None

