"""
Management command to clean up bare host recording URLs.

Removes recording_url values that are bare hosts (e.g., https://transcripts.gotomeeting.com)
without a token, as these are not valid canonical transcript URLs.
"""

from ai_services.models import Meeting
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clean up bare host recording URLs (sets them to NULL)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )
        parser.add_argument(
            "--service-name",
            type=str,
            help="Filter by service_name (e.g., gotomeeting_internal)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        service_name = options.get("service_name")

        # Find meetings with bare host recording URLs
        bare_hosts = [
            "https://transcripts.gotomeeting.com",
            "https://transcripts.gotomeeting.com/",
        ]

        query = Meeting.objects.filter(recording_url__in=bare_hosts)

        # Also find non-canonical transcripts URLs (starts with host but not canonical format)
        non_canonical = Meeting.objects.filter(
            recording_url__startswith="https://transcripts.gotomeeting.com"
        ).exclude(recording_url__startswith="https://transcripts.gotomeeting.com/#/s/")

        # Combine queries
        if service_name:
            query = query.filter(service_name=service_name)
            non_canonical = non_canonical.filter(service_name=service_name)

        all_bare_hosts = list(query) + list(
            non_canonical.exclude(id__in=[m.id for m in query])
        )

        self.stdout.write("=" * 80)
        self.stdout.write("BARE HOST RECORDING URL CLEANUP")
        self.stdout.write("=" * 80)
        self.stdout.write(
            f"Found {len(all_bare_hosts)} meetings with bare host or non-canonical recording URLs"
        )

        if not all_bare_hosts:
            self.stdout.write(
                self.style.SUCCESS("✅ No bare host URLs found. Nothing to clean up.")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n🔍 DRY RUN MODE - No changes will be made\n")
            )
            for meeting in all_bare_hosts[:20]:  # Show first 20
                self.stdout.write(
                    f"  Would clear: meeting_id={meeting.meeting_id}, "
                    f"recording_url={meeting.recording_url}, "
                    f"service_name={meeting.service_name or 'None'}"
                )
            if len(all_bare_hosts) > 20:
                self.stdout.write(f"  ... and {len(all_bare_hosts) - 20} more")
        else:
            # Clear the recording URLs
            updated_count = 0
            for meeting in all_bare_hosts:
                old_url = meeting.recording_url
                meeting.recording_url = None
                meeting.save(update_fields=["recording_url"])
                updated_count += 1
                if updated_count <= 10:
                    self.stdout.write(
                        f"  ✅ Cleared: meeting_id={meeting.meeting_id}, "
                        f"old_url={old_url}"
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Successfully cleared {updated_count} bare host recording URLs"
                )
            )

        self.stdout.write("=" * 80)
