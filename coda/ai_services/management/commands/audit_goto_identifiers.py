"""
Audit GoToMeeting API identifiers to determine correct endpoint usage.

This command:
1. Fetches a small sample of meetings from historicalMeetings API
2. Inspects all available fields (meetingId, meetingInstanceKey, etc.)
3. Tests attendee endpoint with different identifiers
4. Logs which identifier works for each service

Usage:
    poetry run python coda/manage.py audit_goto_identifiers --service internal --days 7 --limit 5
"""

import json
import logging
from datetime import timedelta

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from shared_core.utils.oauth import get_access_token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Audit GoToMeeting API identifiers to determine correct endpoint usage"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service",
            type=str,
            choices=["internal", "external", "both"],
            default="both",
            help="Service to audit (default: both)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to look back (default: 7)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Number of meetings to test per service (default: 5)",
        )

    def handle(self, *args, **options):
        service_option = options["service"]
        days = options["days"]
        limit = options["limit"]

        services_to_audit = []
        if service_option in ["internal", "both"]:
            services_to_audit.append("gotomeeting_internal")
        if service_option in ["external", "both"]:
            services_to_audit.append("gotomeeting_external")

        self.stdout.write(self.style.SUCCESS(f"\n🔍 GoToMeeting Identifier Audit 🔍\n"))
        self.stdout.write(f"Days: {days}")
        self.stdout.write(f"Limit: {limit} meetings per service\n")

        for service_name in services_to_audit:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(f"Auditing: {service_name}")
            self.stdout.write(f"{'='*80}\n")

            # Get access token
            access_token = get_access_token(service_name=service_name)
            if not access_token:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  No OAuth token available for {service_name}. Skipping..."
                    )
                )
                continue

            # Fetch historical meetings
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start_str}&endDate={end_str}"

            try:
                response = requests.get(url=url, headers=headers, timeout=30)
                response.raise_for_status()
                meetings = response.json()

                self.stdout.write(f"📊 Fetched {len(meetings)} meetings from API\n")

                if not meetings:
                    self.stdout.write(f"  No meetings found for {service_name}\n")
                    continue

                # Inspect first meeting structure
                self.stdout.write(f"📋 Sample meeting structure (first meeting):")
                sample_meeting = meetings[0]
                self.stdout.write(json.dumps(sample_meeting, indent=2, default=str))
                self.stdout.write("")

                # Test attendee endpoint for sample meetings
                test_meetings = meetings[:limit]
                self.stdout.write(
                    f"🧪 Testing attendee endpoint for {len(test_meetings)} meetings:\n"
                )

                for i, meeting in enumerate(test_meetings, 1):
                    meeting_id = meeting.get("meetingId")
                    meeting_instance_key = meeting.get("meetingInstanceKey")
                    subject = meeting.get("subject", "N/A")
                    start_time = meeting.get("startTime", "N/A")

                    self.stdout.write(f"\n{i}. Meeting: {subject}")
                    self.stdout.write(f"   meetingId: {meeting_id}")
                    self.stdout.write(f"   meetingInstanceKey: {meeting_instance_key}")
                    self.stdout.write(f"   startTime: {start_time}")

                    # Test with meetingId
                    if meeting_id:
                        test_url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees"
                        test_response = requests.get(
                            url=test_url, headers=headers, timeout=10
                        )
                        status = test_response.status_code
                        self.stdout.write(
                            f"   ✅ /meetings/{meeting_id}/attendees → HTTP {status}"
                        )

                        if status == 200:
                            attendees = test_response.json()
                            self.stdout.write(f"      Found {len(attendees)} attendees")
                            if attendees:
                                sample_attendee = attendees[0]
                                self.stdout.write(
                                    f"      Sample attendee keys: {list(sample_attendee.keys())}"
                                )
                        elif status == 404:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"      ❌ 404 Not Found - meetingId does NOT work"
                                )
                            )

                    # Test with meetingInstanceKey if available
                    if meeting_instance_key and meeting_instance_key != meeting_id:
                        test_url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_instance_key}/attendees"
                        test_response = requests.get(
                            url=test_url, headers=headers, timeout=10
                        )
                        status = test_response.status_code
                        self.stdout.write(
                            f"   ✅ /meetings/{meeting_instance_key}/attendees → HTTP {status}"
                        )

                        if status == 200:
                            attendees = test_response.json()
                            self.stdout.write(f"      Found {len(attendees)} attendees")
                            if attendees:
                                sample_attendee = attendees[0]
                                self.stdout.write(
                                    f"      Sample attendee keys: {list(sample_attendee.keys())}"
                                )
                        elif status == 404:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"      ❌ 404 Not Found - meetingInstanceKey does NOT work"
                                )
                            )

                    # Show all available fields
                    self.stdout.write(
                        f"   📋 All available fields: {list(meeting.keys())}"
                    )

                # Summary
                self.stdout.write(f"\n{'='*80}")
                self.stdout.write(f"Summary for {service_name}:")
                self.stdout.write(f"{'='*80}\n")

                # Count which identifier works
                meeting_id_works = 0
                instance_key_works = 0
                both_work = 0
                neither_work = 0

                for meeting in test_meetings:
                    meeting_id = meeting.get("meetingId")
                    meeting_instance_key = meeting.get("meetingInstanceKey")

                    meeting_id_ok = False
                    instance_key_ok = False

                    if meeting_id:
                        test_url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees"
                        test_response = requests.get(
                            url=test_url, headers=headers, timeout=10
                        )
                        if test_response.status_code == 200:
                            meeting_id_ok = True

                    if meeting_instance_key and meeting_instance_key != meeting_id:
                        test_url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_instance_key}/attendees"
                        test_response = requests.get(
                            url=test_url, headers=headers, timeout=10
                        )
                        if test_response.status_code == 200:
                            instance_key_ok = True

                    if meeting_id_ok and instance_key_ok:
                        both_work += 1
                    elif meeting_id_ok:
                        meeting_id_works += 1
                    elif instance_key_ok:
                        instance_key_works += 1
                    else:
                        neither_work += 1

                self.stdout.write(f"  meetingId works: {meeting_id_works}")
                self.stdout.write(f"  meetingInstanceKey works: {instance_key_works}")
                self.stdout.write(f"  Both work: {both_work}")
                self.stdout.write(f"  Neither works: {neither_work}")

            except requests.exceptions.HTTPError as e:
                self.stdout.write(self.style.ERROR(f"❌ HTTP error: {e}"))
                if e.response.status_code == 401:
                    self.stdout.write("   OAuth token expired or invalid")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                logger.exception("Error in audit_goto_identifiers")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Audit complete!\n"))
