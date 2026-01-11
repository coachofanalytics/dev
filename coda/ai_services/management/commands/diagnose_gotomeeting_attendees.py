"""
Management command to diagnose GoToMeeting attendee fetching.

Fetches raw API data for a specific meeting and dumps it to JSON file.
Read-only diagnostic - no database writes.

Diagnoses:
1. Checks if meeting exists via /G2M/rest/meetings/{meeting_id}
2. Fetches attendees via /G2M/rest/meetings/{meeting_id}/attendees
3. Optionally queries meeting list to verify meeting_id appears in API response
"""

import json
import os
from datetime import timedelta
from pathlib import Path

import requests
from ai_services.models import Meeting
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone
from shared_core.utils.oauth import get_access_token


class Command(BaseCommand):
    help = "Diagnose GoToMeeting attendee fetching for a specific meeting (read-only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--meeting-id",
            type=str,
            help="GoToMeeting meeting_id to diagnose",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days to look back if meeting-id not provided (default: 90)",
        )
        parser.add_argument(
            "--since",
            type=str,
            help="Start date (YYYY-MM-DD) to look back from today. Overrides --days if provided.",
        )
        parser.add_argument(
            "--check-meeting-list",
            action="store_true",
            help="Also query meeting list API to verify meeting_id appears in response",
        )

    def handle(self, *args, **options):
        meeting_id = options.get("meeting_id")
        days = options.get("days", 90)
        since_date_str = options.get("since")
        check_meeting_list = options.get("check_meeting_list", False)

        # Create diagnostics directory
        diagnostics_dir = Path("_diagnostics/gotomeeting")
        diagnostics_dir.mkdir(parents=True, exist_ok=True)

        # If no meeting_id provided, find a meeting with 0 attendees
        db_meeting = None
        if not meeting_id:
            # Calculate cutoff date
            if since_date_str:
                try:
                    from datetime import datetime

                    since_date = datetime.strptime(since_date_str, "%Y-%m-%d").date()
                    cutoff_date = timezone.make_aware(
                        datetime.combine(since_date, datetime.min.time())
                    )
                    self.stdout.write(f"Using --since date: {since_date_str}")
                except ValueError:
                    self.stdout.write(
                        self.style.ERROR(f"Invalid --since date format. Use YYYY-MM-DD")
                    )
                    return
            else:
                cutoff_date = timezone.now() - timedelta(days=days)
            db_meeting = (
                Meeting.objects.filter(start_time__gte=cutoff_date)
                .annotate(db_attendee_count=models.Count("attendees"))
                .filter(db_attendee_count=0)
                .first()
            )

            if not db_meeting:
                self.stdout.write(
                    self.style.WARNING(
                        f"No meetings with 0 attendees found in last {days} days"
                    )
                )
                return

            meeting_id = db_meeting.meeting_id
            self.stdout.write(f"Using meeting_id from DB: {meeting_id}")
            self.stdout.write(f"  Topic: {db_meeting.topic}")
            self.stdout.write(f"  Start: {db_meeting.start_time}")
            self.stdout.write(f"  Service: {db_meeting.service_name or 'N/A'}")
            self.stdout.write()
        else:
            # Try to get DB meeting for context
            try:
                db_meeting = Meeting.objects.get(meeting_id=meeting_id)
            except Meeting.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Meeting {meeting_id} not found in DB")
                )

        # Get access token (try multiple service names)
        access_token = None
        service_name = None

        # If DB meeting exists, try its service_name first
        if db_meeting and db_meeting.service_name:
            token = get_access_token(service_name=db_meeting.service_name)
            if token:
                access_token = token
                service_name = db_meeting.service_name

        # Fallback to standard service names
        if not access_token:
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

        headers = {"Authorization": f"Bearer {access_token}"}

        # STEP 1: Check if meeting exists via /G2M/rest/meetings/{meeting_id}
        self.stdout.write("=" * 80)
        self.stdout.write("STEP 1: CHECK MEETING EXISTENCE")
        self.stdout.write("=" * 80)

        meeting_url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}"
        self.stdout.write(f"GET {meeting_url}")

        meeting_exists = False
        meeting_data = None

        try:
            response = requests.get(url=meeting_url, headers=headers, timeout=30)

            if response.status_code == 200:
                meeting_data = response.json()
                meeting_exists = True

                # Handle both dict and list responses
                if isinstance(meeting_data, list):
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  API returned list (length: {len(meeting_data)}) instead of dict"
                        )
                    )
                    if meeting_data:
                        meeting_data = meeting_data[0]  # Use first item
                        self.stdout.write(f"   Using first item from list")
                    else:
                        meeting_data = {}
                        meeting_exists = False

                # Save to file
                meeting_file = diagnostics_dir / f"{meeting_id}_meeting.json"
                with open(meeting_file, "w") as f:
                    json.dump(meeting_data, f, indent=2)

                if meeting_exists:
                    self.stdout.write(self.style.SUCCESS(f"✅ Meeting exists in API"))
                    self.stdout.write(f"   Status: {response.status_code}")
                    self.stdout.write(
                        f"   Response type: {type(meeting_data).__name__}"
                    )
                    self.stdout.write(f"   Raw JSON saved to: {meeting_file}")

                    # Print summary (only if dict)
                    if isinstance(meeting_data, dict):
                        subject = meeting_data.get("subject") or meeting_data.get(
                            "topic", "N/A"
                        )
                        start_time = meeting_data.get("startTime") or meeting_data.get(
                            "start_time", "N/A"
                        )
                        self.stdout.write(f"   Subject: {subject}")
                        self.stdout.write(f"   Start Time: {start_time}")

            elif response.status_code == 404:
                self.stdout.write(self.style.ERROR(f"❌ Meeting NOT found in API"))
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   Response: {response.text[:200]}")

            elif response.status_code == 401:
                self.stdout.write(self.style.ERROR(f"❌ Unauthorized"))
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   OAuth token expired or invalid")

            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Unexpected status"))
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   Response: {response.text[:200]}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error checking meeting existence: {e}")
            )

        self.stdout.write()

        # STEP 2: Check meeting list if requested
        if check_meeting_list and db_meeting:
            self.stdout.write("=" * 80)
            self.stdout.write("STEP 2: CHECK MEETING LIST API")
            self.stdout.write("=" * 80)

            # Query ±3 days around meeting start_time
            window_start = db_meeting.start_time - timedelta(days=3)
            window_end = db_meeting.start_time + timedelta(days=3)

            start_str = window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_str = window_end.strftime("%Y-%m-%dT%H:%M:%SZ")

            list_url = f"https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start_str}&endDate={end_str}"
            self.stdout.write(f"GET {list_url}")
            self.stdout.write(f"   Window: {window_start} to {window_end}")

            try:
                response = requests.get(url=list_url, headers=headers, timeout=30)

                if response.status_code == 200:
                    meetings_list = response.json()

                    # Save to file
                    list_file = diagnostics_dir / f"{meeting_id}_meeting_list.json"
                    with open(list_file, "w") as f:
                        json.dump(meetings_list, f, indent=2)

                    self.stdout.write(self.style.SUCCESS(f"✅ Meeting list fetched"))
                    self.stdout.write(f"   Status: {response.status_code}")
                    self.stdout.write(f"   Meetings in window: {len(meetings_list)}")
                    self.stdout.write(f"   Raw JSON saved to: {list_file}")

                    # Check if our meeting_id appears
                    found_meeting_ids = [
                        m.get("meetingId") for m in meetings_list if m.get("meetingId")
                    ]
                    if meeting_id in found_meeting_ids:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"   ✅ DB meeting_id {meeting_id} FOUND in API response"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"   ⚠️  DB meeting_id {meeting_id} NOT FOUND in API response"
                            )
                        )
                        self.stdout.write(
                            f"   Found meetingIds: {found_meeting_ids[:10]}"
                        )

                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to fetch meeting list")
                    )
                    self.stdout.write(f"   Status: {response.status_code}")
                    self.stdout.write(f"   Response: {response.text[:200]}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error fetching meeting list: {e}"))

            self.stdout.write()

        # STEP 3: Fetch attendees from API
        self.stdout.write("=" * 80)
        self.stdout.write("STEP 3: FETCH ATTENDEES")
        self.stdout.write("=" * 80)

        attendee_url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees"
        self.stdout.write(f"GET {attendee_url}")

        try:
            response = requests.get(url=attendee_url, headers=headers, timeout=30)

            if response.status_code == 200:
                attendees_data = response.json()

                # Dump to JSON file
                json_file = diagnostics_dir / f"{meeting_id}_attendees.json"
                with open(json_file, "w") as f:
                    json.dump(attendees_data, f, indent=2)

                self.stdout.write(self.style.SUCCESS(f"✅ Attendees fetched"))
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   Raw JSON saved to: {json_file}")
                self.stdout.write()

                # Print summary
                self.stdout.write("API RESPONSE SUMMARY")
                self.stdout.write("-" * 80)
                self.stdout.write(f"api_attendee_count: {len(attendees_data)}")
                self.stdout.write(f"where_attendees_found: response.json() (list)")
                self.stdout.write()

                if attendees_data:
                    self.stdout.write("Sample attendees (first 3):")
                    for i, attendee in enumerate(attendees_data[:3], 1):
                        name = attendee.get("name") or attendee.get(
                            "attendeeName", "N/A"
                        )
                        email = attendee.get("email") or attendee.get(
                            "attendeeEmail", "N/A"
                        )
                        instance_key = attendee.get(
                            "meetingInstanceKey"
                        ) or attendee.get("meeting_instance_key", "N/A")
                        is_org = attendee.get("isOrganizer") or attendee.get(
                            "is_organizer", False
                        )
                        self.stdout.write(
                            f"  {i}. name: {name}, email: {email}, instanceKey: {instance_key}, isOrganizer: {is_org}"
                        )
                else:
                    self.stdout.write("  (no attendees in API response)")

            elif response.status_code == 404:
                self.stdout.write(
                    self.style.ERROR(f"❌ Attendees endpoint returned 404")
                )
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   Response: {response.text[:200]}")

            elif response.status_code == 401:
                self.stdout.write(self.style.ERROR(f"❌ Unauthorized"))
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   OAuth token expired or invalid")

            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Unexpected status"))
                self.stdout.write(f"   Status: {response.status_code}")
                self.stdout.write(f"   Response: {response.text[:200]}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching attendees: {e}"))

        self.stdout.write()

        # STEP 4: Print conclusions
        self.stdout.write("=" * 80)
        self.stdout.write("CONCLUSIONS")
        self.stdout.write("=" * 80)

        if not meeting_exists:
            self.stdout.write(
                self.style.ERROR(
                    "❌ DB meeting_id not found via /meetings => wrong identifier OR wrong organizer scope"
                )
            )
            self.stdout.write()
            self.stdout.write("Most likely fix location:")
            self.stdout.write("  File: coda/ai_services/views.py")
            self.stdout.write("  Function: save_meeting_data()")
            self.stdout.write("  Line: 459")
            self.stdout.write(
                "  Code: meeting_id = meeting_info.get('meetingId') or meeting_info.get('meeting_id', '')"
            )
            self.stdout.write()
            self.stdout.write("  The meeting_id is extracted from:")
            self.stdout.write(
                "  - File: coda/ai_services/services/goto_meeting_sync_service.py"
            )
            self.stdout.write("  - Function: fetch_meetings()")
            self.stdout.write("  - Line: 58")
            self.stdout.write("  - Code: meeting_id = meeting.get('meetingId')")
            self.stdout.write()
            self.stdout.write("  The API endpoint used is:")
            self.stdout.write(
                "  - GET https://api.getgo.com/G2M/rest/historicalMeetings?startDate={start}&endDate={end}"
            )
            self.stdout.write()
            self.stdout.write(
                "  ISSUE: The meetingId from historicalMeetings may not be valid for the"
            )
            self.stdout.write(
                "  /meetings/{meeting_id} or /meetings/{meeting_id}/attendees endpoints if"
            )
            self.stdout.write(
                "  the meeting belongs to a different organizer/account scope."
            )

        elif check_meeting_list and db_meeting:
            # Check if we found it in the list
            # (This would be set in the meeting list check above)
            pass

        else:
            self.stdout.write("✅ Meeting exists in API")
            if db_meeting and db_meeting.attendee_count == 0:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️  Meeting exists but attendees missing => endpoint/object mismatch OR sync bug"
                    )
                )
                self.stdout.write()
                self.stdout.write("Most likely fix location:")
                self.stdout.write(
                    "  File: coda/ai_services/services/attendee_sync_service.py"
                )
                self.stdout.write("  Function: fetch_attendees_for_meeting()")
                self.stdout.write("  Line: 242")
                self.stdout.write(
                    '  Code: url = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees"'
                )
                self.stdout.write()
                self.stdout.write(
                    "  The endpoint may require filtering by meetingInstanceKey or sessionId."
                )
                self.stdout.write(
                    "  Check if the meeting has a sessionId stored in DB and use that for filtering."
                )

        self.stdout.write()
        self.stdout.write("=" * 80)
