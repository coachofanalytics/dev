"""
Diagnostic command to identify root cause of attendee sync issues.

Run this to understand:
1. Whether attendees are being fetched but not saved
2. Whether the wrong identifier is being used (meeting_id vs session_id)
3. Whether attendees are stored but not linked correctly
4. Whether combined names need normalization

Usage:
    poetry run python coda/manage.py diagnose_attendee_sync
    poetry run python coda/manage.py diagnose_attendee_sync --service internal
"""

from datetime import timedelta

from ai_services.models import Meeting, MeetingAttendee
from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Q
from django.utils import timezone


class Command(BaseCommand):
    help = "Diagnose attendee sync issues"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "all"],
            default="all",
            help="Service to diagnose (default: all)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to look back (default: 30)",
        )

    def handle(self, *args, **options):
        service_option = options["service"]
        days = options["days"]

        # Map service option
        if service_option == "internal":
            service_name = "gotomeeting_internal"
        elif service_option == "external":
            service_name = "gotomeeting_external"
        else:
            service_name = None

        self.stdout.write(
            self.style.SUCCESS(f"\n🔍 Attendee Sync Diagnostic Report 🔍\n")
        )
        self.stdout.write(f"Service: {service_option}")
        self.stdout.write(f"Days: {days}\n")

        # Date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Query meetings
        meetings_query = Meeting.objects.filter(
            start_time__gte=start_date, start_time__lte=end_date
        )

        if service_name:
            meetings_query = meetings_query.filter(service_name=service_name)

        meetings = meetings_query.order_by("-start_time")

        # 1) Check meeting timestamps vs attendee timestamps
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"1. Meeting vs Attendee Timestamp Analysis")
        self.stdout.write(f"{'='*80}\n")

        meetings_with_attendees = meetings.annotate(
            attendee_count_db=Count("attendees"),
            latest_attendee_update=Max("attendees__updated_at"),
        )

        stale_attendees = []
        fresh_attendees = []
        no_attendees = []

        for meeting in meetings_with_attendees[:50]:  # Sample first 50
            if meeting.attendee_count_db == 0:
                no_attendees.append(meeting)
            else:
                latest_attendee_update = meeting.latest_attendee_update
                if latest_attendee_update:
                    days_since_update = (timezone.now() - latest_attendee_update).days
                    if days_since_update > 7:  # Stale if >7 days old
                        stale_attendees.append((meeting, days_since_update))
                    else:
                        fresh_attendees.append(meeting)

        self.stdout.write(f"Meetings with NO attendees: {len(no_attendees)}")
        self.stdout.write(
            f"Meetings with STALE attendees (>7 days old): {len(stale_attendees)}"
        )
        self.stdout.write(f"Meetings with FRESH attendees: {len(fresh_attendees)}\n")

        if stale_attendees:
            self.stdout.write(f"Sample stale attendee meetings:")
            for meeting, days_old in stale_attendees[:5]:
                self.stdout.write(
                    f"  - Meeting {meeting.meeting_id}: {meeting.topic[:50]} "
                    f"(attendees updated {days_old} days ago, meeting updated {meeting.updated_at.date()})"
                )

        if no_attendees:
            self.stdout.write(f"\nSample meetings with NO attendees:")
            for meeting in no_attendees[:5]:
                self.stdout.write(
                    f"  - Meeting {meeting.meeting_id}: {meeting.topic[:50]} "
                    f"(updated {meeting.updated_at.date()})"
                )

        # 2) Check attendee data quality
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"2. Attendee Data Quality Analysis")
        self.stdout.write(f"{'='*80}\n")

        all_attendees = MeetingAttendee.objects.filter(meeting__in=meetings)

        total_attendees = all_attendees.count()
        attendees_with_email = all_attendees.exclude(
            attendee_email__startswith="no-email-"
        ).count()
        attendees_without_email = total_attendees - attendees_with_email

        # Check for combined names (e.g., "EUNICE, JUDY AND NOREEN")
        combined_name_patterns = all_attendees.filter(
            Q(attendee_name__icontains=",")
            | Q(attendee_name__icontains=" AND ")
            | Q(attendee_name__icontains=" & ")
        )

        self.stdout.write(f"Total attendees: {total_attendees}")
        self.stdout.write(f"  With email: {attendees_with_email}")
        self.stdout.write(f"  Without email (placeholder): {attendees_without_email}")
        self.stdout.write(
            f"  Combined names (needs splitting): {combined_name_patterns.count()}\n"
        )

        if combined_name_patterns.exists():
            self.stdout.write(f"Sample combined names:")
            for attendee in combined_name_patterns[:5]:
                self.stdout.write(
                    f"  - '{attendee.attendee_name}' (Meeting: {attendee.meeting.meeting_id})"
                )

        # 3) Check meeting_id format vs potential session_id
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"3. Meeting ID Format Analysis")
        self.stdout.write(f"{'='*80}\n")

        # Sample meeting IDs to see format
        sample_meetings = meetings[:10]
        self.stdout.write(f"Sample meeting_id formats:")
        for meeting in sample_meetings:
            self.stdout.write(
                f"  - {meeting.meeting_id} (length: {len(meeting.meeting_id)})"
            )

        # 4) Check for duplicate attendees (same meeting, different emails)
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"4. Duplicate Attendee Analysis")
        self.stdout.write(f"{'='*80}\n")

        # Group by meeting and attendee_name to find potential duplicates
        duplicate_candidates = (
            MeetingAttendee.objects.filter(meeting__in=meetings)
            .values("meeting_id", "attendee_name")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        self.stdout.write(
            f"Potential duplicate attendees (same name, different emails): {duplicate_candidates.count()}\n"
        )

        if duplicate_candidates.exists():
            self.stdout.write(f"Sample duplicates:")
            for dup in duplicate_candidates[:5]:
                meeting = Meeting.objects.get(id=dup["meeting_id"])
                attendees = MeetingAttendee.objects.filter(
                    meeting_id=dup["meeting_id"], attendee_name=dup["attendee_name"]
                )
                self.stdout.write(
                    f"  - Meeting {meeting.meeting_id}: '{dup['attendee_name']}' "
                    f"appears {dup['count']} times with emails: {', '.join([a.attendee_email for a in attendees])}"
                )

        # 5) Summary and recommendations
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"5. Root Cause Analysis")
        self.stdout.write(f"{'='*80}\n")

        if len(stale_attendees) > len(fresh_attendees):
            self.stdout.write("⚠️  ROOT CAUSE: Attendees are STALE (not being updated)")
            self.stdout.write(
                "   - Attendee sync is likely NOT running or failing silently"
            )
            self.stdout.write("   - Check if attendee API endpoint is being called")
            self.stdout.write(
                "   - Verify API endpoint uses correct identifier (meeting_id vs session_id)"
            )

        if len(no_attendees) > len(meetings) * 0.5:
            self.stdout.write("⚠️  ROOT CAUSE: Many meetings have NO attendees")
            self.stdout.write("   - Attendee fetching may be failing for most meetings")
            self.stdout.write("   - Check API error logs")
            self.stdout.write("   - Verify attendee endpoint URL format")

        if combined_name_patterns.count() > 0:
            self.stdout.write("⚠️  ROOT CAUSE: Combined attendee names detected")
            self.stdout.write("   - Need to split names like 'EUNICE, JUDY AND NOREEN'")
            self.stdout.write("   - Implement name normalization/splitting logic")

        # 6) DB Verification Statistics
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"6. DB Verification Statistics")
        self.stdout.write(f"{'='*80}\n")

        # Meetings count by service (Count and Max already imported at top)
        meetings_by_service = (
            Meeting.objects.filter(start_time__gte=start_date, start_time__lte=end_date)
            .values("service_name")
            .annotate(meeting_count=Count("id"))
            .order_by("service_name")
        )

        self.stdout.write("Meetings count by service:")
        for item in meetings_by_service:
            svc = item["service_name"] or "NULL"
            count = item["meeting_count"]
            self.stdout.write(f"  {svc}: {count} meetings")

        # Attendees count by service
        attendees_by_service = (
            MeetingAttendee.objects.filter(
                meeting__start_time__gte=start_date, meeting__start_time__lte=end_date
            )
            .values("meeting__service_name")
            .annotate(attendee_count=Count("id"))
            .order_by("meeting__service_name")
        )

        self.stdout.write("\nAttendees count by service:")
        for item in attendees_by_service:
            svc = item["meeting__service_name"] or "NULL"
            count = item["attendee_count"]
            self.stdout.write(f"  {svc}: {count} attendees")

        # MAX(attendee.updated_at) by service
        latest_by_service = (
            MeetingAttendee.objects.filter(
                meeting__start_time__gte=start_date, meeting__start_time__lte=end_date
            )
            .values("meeting__service_name")
            .annotate(latest_update=Max("updated_at"))
            .order_by("meeting__service_name")
        )

        self.stdout.write("\nLatest attendee update by service:")
        for item in latest_by_service:
            svc = item["meeting__service_name"] or "NULL"
            latest = item["latest_update"]
            if latest:
                days_ago = (timezone.now() - latest).days
                self.stdout.write(
                    f"  {svc}: {latest.strftime('%Y-%m-%d %H:%M:%S')} ({days_ago} days ago)"
                )
            else:
                self.stdout.write(f"  {svc}: No attendees")

        # Top 10 meetings by attendee count (using attendee_count_db annotation)
        top_meetings = Meeting.objects.filter(
            start_time__gte=start_date, start_time__lte=end_date
        )
        if service_name:
            top_meetings = top_meetings.filter(service_name=service_name)

        top_meetings = top_meetings.annotate(
            attendee_count_db=Count("attendees")
        ).order_by("-attendee_count_db")[:10]

        self.stdout.write("\nTop 10 meetings by attendee count:")
        for meeting in top_meetings:
            self.stdout.write(
                f"  Meeting {meeting.meeting_id}: {meeting.topic[:50] if meeting.topic else 'N/A'} "
                f"({meeting.service_name or 'NULL'}, {meeting.start_time.date()}, "
                f"{meeting.attendee_count_db} attendees)"
            )

            # Sample attendee names for top meeting
            if meeting.attendee_count_db > 0:
                sample_attendees = MeetingAttendee.objects.filter(
                    meeting=meeting
                ).values_list("attendee_name", flat=True)[:10]
                self.stdout.write(
                    f"    Sample attendees: {', '.join(sample_attendees)}"
                )

        # 7) Attendee Count Distribution and Instance Key Status
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"7. Attendee Count Distribution & Instance Key Status")
        self.stdout.write(f"{'='*80}\n")

        # Attendee count distribution by service
        meetings_with_counts = Meeting.objects.filter(
            start_time__gte=start_date, start_time__lte=end_date
        )
        if service_name:
            meetings_with_counts = meetings_with_counts.filter(
                service_name=service_name
            )

        meetings_with_counts = meetings_with_counts.annotate(
            attendee_count_db=Count("attendees")
        )

        # Distribution buckets: 0, 1, 2, 3, 4+
        distribution = {0: 0, 1: 0, 2: 0, 3: 0, "4+": 0}
        for meeting in meetings_with_counts:
            count = meeting.attendee_count_db
            if count == 0:
                distribution[0] += 1
            elif count == 1:
                distribution[1] += 1
            elif count == 2:
                distribution[2] += 1
            elif count == 3:
                distribution[3] += 1
            else:
                distribution["4+"] += 1

        self.stdout.write("Attendee count distribution:")
        for bucket, count in distribution.items():
            self.stdout.write(f"  {bucket} attendees: {count} meetings")

        # Missing instance keys
        missing_instance_keys = meetings_with_counts.filter(
            Q(provider_meeting_instance_key__isnull=True)
            | Q(provider_meeting_instance_key="")
        ).count()
        self.stdout.write(
            f"\nMeetings missing provider_meeting_instance_key: {missing_instance_keys}"
        )

        # Meetings with instance keys
        with_instance_keys = meetings_with_counts.exclude(
            Q(provider_meeting_instance_key__isnull=True)
            | Q(provider_meeting_instance_key="")
        ).count()
        self.stdout.write(
            f"Meetings with provider_meeting_instance_key: {with_instance_keys}"
        )

        # Provider not found (404) statistics
        provider_not_found_count = meetings_with_counts.filter(
            provider_not_found=True
        ).count()
        if provider_not_found_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Meetings marked as provider_not_found (404): {provider_not_found_count}"
                )
            )

            # Show top recent 404 meetingIds
            recent_404 = Meeting.objects.filter(
                provider_not_found=True,
                start_time__gte=start_date,
                start_time__lte=end_date,
            )
            if service_name:
                recent_404 = recent_404.filter(service_name=service_name)

            recent_404 = recent_404.order_by("-provider_not_found_at")[:10]

            if recent_404:
                self.stdout.write("   Top 10 recent 404 meetingIds:")
                for m in recent_404:
                    self.stdout.write(
                        f"      - {m.meeting_id} (service={m.service_name}, marked_at={m.provider_not_found_at})"
                    )
        else:
            self.stdout.write(f"\n✅ No meetings marked as provider_not_found")

        # 8) SQL queries for manual verification
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"8. Verification SQL Queries")
        self.stdout.write(f"{'='*80}\n")

        self.stdout.write("-- Count attendees by service")
        self.stdout.write("SELECT service_name, COUNT(*) as meeting_count, ")
        self.stdout.write(
            "       SUM((SELECT COUNT(*) FROM ai_services_meetingattendee WHERE meeting_id = m.id)) as attendee_count"
        )
        self.stdout.write("FROM ai_services_meeting m")
        self.stdout.write(
            f"WHERE m.start_time >= '{start_date.date()}' AND m.start_time <= '{end_date.date()}'"
        )
        if service_name:
            self.stdout.write(f"  AND m.service_name = '{service_name}'")
        self.stdout.write("GROUP BY service_name;\n")

        self.stdout.write("-- Latest attendee update timestamps")
        self.stdout.write("SELECT MAX(updated_at) as latest_attendee_update")
        self.stdout.write("FROM ai_services_meetingattendee ma")
        self.stdout.write("JOIN ai_services_meeting m ON ma.meeting_id = m.id")
        self.stdout.write(
            f"WHERE m.start_time >= '{start_date.date()}' AND m.start_time <= '{end_date.date()}'"
        )
        if service_name:
            self.stdout.write(f"  AND m.service_name = '{service_name}'")
        self.stdout.write(";\n")

        self.stdout.write("-- Top meetings by attendee count")
        self.stdout.write(
            "SELECT m.meeting_id, m.topic, m.service_name, COUNT(ma.id) as attendee_count"
        )
        self.stdout.write("FROM ai_services_meeting m")
        self.stdout.write(
            "LEFT JOIN ai_services_meetingattendee ma ON m.id = ma.meeting_id"
        )
        self.stdout.write(
            f"WHERE m.start_time >= '{start_date.date()}' AND m.start_time <= '{end_date.date()}'"
        )
        if service_name:
            self.stdout.write(f"  AND m.service_name = '{service_name}'")
        self.stdout.write("GROUP BY m.id, m.meeting_id, m.topic, m.service_name")
        self.stdout.write("ORDER BY attendee_count DESC")
        self.stdout.write("LIMIT 10;\n")

        self.stdout.write("-- Provider not found (404) meetings")
        self.stdout.write("SELECT service_name, COUNT(*) as count")
        self.stdout.write("FROM ai_services_meeting")
        self.stdout.write("WHERE provider_not_found = TRUE")
        if service_name:
            self.stdout.write(f"  AND service_name = '{service_name}'")
        self.stdout.write("GROUP BY service_name;\n")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Diagnostic complete!\n"))
