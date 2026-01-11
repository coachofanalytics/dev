"""
Management command to diagnose gaps between API and DB attendee counts.

Compares GoToMeeting API attendee data vs database for meetings with 0 attendees.
Read-only diagnostic - no database writes.
"""

import json
import os
from datetime import timedelta
from pathlib import Path

import requests
from ai_services.models import Meeting, MeetingAttendee
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from shared_core.utils.oauth import get_access_token


class Command(BaseCommand):
    help = "Diagnose gaps between API and DB attendee counts (read-only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days to analyze (default: 90)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of meetings to check (default: 10)",
        )

    def handle(self, *args, **options):
        days = options.get("days", 90)
        limit = options.get("limit", 10)

        cutoff_date = timezone.now() - timedelta(days=days)

        # Find meetings with 0 attendees
        meetings = (
            Meeting.objects.filter(start_time__gte=cutoff_date)
            .annotate(db_attendee_count=Count("attendees"))
            .filter(db_attendee_count=0)
            .order_by("-start_time")[:limit]
        )

        if not meetings.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"No meetings with 0 attendees found in last {days} days"
                )
            )
            return

        self.stdout.write("=" * 80)
        self.stdout.write("GOTOMEETING ATTENDEE GAP DIAGNOSTIC")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Scope: Last {days} days")
        self.stdout.write(f"Checking {meetings.count()} meetings with 0 DB attendees")
        self.stdout.write()

        # Get access token (try multiple service names)
        access_token = None
        service_name = None

        for svc in ["gotomeeting_external", "gotomeeting_internal", "gotomeeting"]:
            token = get_access_token(service_name=svc)
            if token:
                access_token = token
                service_name = svc
                break

        if not access_token:
            self.stdout.write(
                self.style.ERROR("No OAuth token available. Please authenticate first.")
            )
            return

        self.stdout.write(f"Using OAuth token for service: {service_name}")
        self.stdout.write()

        # Process each meeting
        headers = {"Authorization": f"Bearer {access_token}"}

        results = []

        for meeting in meetings:
            self.stdout.write("-" * 80)
            self.stdout.write(f"Meeting ID: {meeting.meeting_id}")
            self.stdout.write(f"  Topic: {meeting.topic[:60]}...")
            self.stdout.write(f"  Start: {meeting.start_time}")
            self.stdout.write(f"  Service: {meeting.service_name or 'N/A'}")
            db_count = meeting.db_attendee_count
            self.stdout.write(f"  DB attendee_count: {db_count}")

            # Fetch from API
            url = f"https://api.getgo.com/G2M/rest/meetings/{meeting.meeting_id}/attendees"

            try:
                response = requests.get(url=url, headers=headers, timeout=30)

                if response.status_code == 200:
                    attendees_data = response.json()
                    api_count = len(attendees_data)

                    self.stdout.write(f"  API attendee_count: {api_count}")

                    # Determine conclusion
                    if api_count > 0 and db_count == 0:
                        conclusion = (
                            "API has attendees but DB has none => transform/persist bug"
                        )
                        self.stdout.write(
                            self.style.WARNING(f"  Conclusion: {conclusion}")
                        )

                        # Show sample attendees
                        if attendees_data:
                            self.stdout.write("  Sample API attendees:")
                            for i, att in enumerate(attendees_data[:3], 1):
                                name = att.get("name") or att.get("attendeeName", "N/A")
                                email = att.get("email") or att.get(
                                    "attendeeEmail", "N/A"
                                )
                                instance_key = att.get("meetingInstanceKey") or att.get(
                                    "meeting_instance_key", "N/A"
                                )
                                self.stdout.write(
                                    f"    {i}. {name} ({email}) [instanceKey: {instance_key}]"
                                )

                    elif api_count == 0 and db_count == 0:
                        conclusion = "API has none => endpoint/timing/scopes issue"
                        self.stdout.write(
                            self.style.WARNING(f"  Conclusion: {conclusion}")
                        )

                    else:
                        conclusion = "Unexpected state"
                        self.stdout.write(
                            self.style.ERROR(f"  Conclusion: {conclusion}")
                        )

                    results.append(
                        {
                            "meeting_id": meeting.meeting_id,
                            "topic": meeting.topic,
                            "start_time": meeting.start_time.isoformat(),
                            "db_attendee_count": db_count,
                            "api_attendee_count": api_count,
                            "conclusion": conclusion,
                        }
                    )

                elif response.status_code == 404:
                    conclusion = (
                        "API has none => endpoint/timing/scopes issue (404 Not Found)"
                    )
                    self.stdout.write(f"  API attendee_count: N/A (404 Not Found)")
                    self.stdout.write(self.style.WARNING(f"  Conclusion: {conclusion}"))

                    results.append(
                        {
                            "meeting_id": meeting.meeting_id,
                            "topic": meeting.topic,
                            "start_time": meeting.start_time.isoformat(),
                            "db_attendee_count": db_count,
                            "api_attendee_count": 0,
                            "conclusion": conclusion,
                        }
                    )

                elif response.status_code == 401:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  API Error: 401 Unauthorized (token expired)"
                        )
                    )
                    break

                else:
                    self.stdout.write(
                        self.style.ERROR(f"  API Error: {response.status_code}")
                    )
                    self.stdout.write(f"  Response: {response.text[:200]}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error fetching API data: {e}"))

            self.stdout.write()

        # Summary
        self.stdout.write("=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)

        transform_bugs = [
            r for r in results if "transform/persist bug" in r["conclusion"]
        ]
        api_issues = [
            r for r in results if "endpoint/timing/scopes issue" in r["conclusion"]
        ]

        self.stdout.write(f"Total meetings checked: {len(results)}")
        self.stdout.write(f"  Transform/persist bugs: {len(transform_bugs)}")
        self.stdout.write(f"  API endpoint/timing/scopes issues: {len(api_issues)}")
        self.stdout.write()

        if transform_bugs:
            self.stdout.write("Meetings with transform/persist bugs:")
            for r in transform_bugs:
                self.stdout.write(
                    f"  - {r['meeting_id']}: {r['topic'][:50]}... (API: {r['api_attendee_count']}, DB: {r['db_attendee_count']})"
                )

        self.stdout.write()
        self.stdout.write("=" * 80)
