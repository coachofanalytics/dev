"""
Management command to run daily AI operations.

Runs AI-1 (meeting tagging), AI-2 (requirement matching), and AI-3 (review suggestions)
in batch mode and stores results in AIOperationsRun for observability.
"""

import csv
import os

from ai_services.services.ai_operations_service import AIOperationsService
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Run daily AI operations (AI-1, AI-2, AI-3) and store results"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Number of days to look back (default: 1)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional limit on number of items to process",
        )
        parser.add_argument(
            "--service",
            type=str,
            default=None,
            help='Optional service filter (e.g., "external", "internal")',
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode (count only, no actual changes)",
        )
        parser.add_argument(
            "--export",
            type=str,
            default=None,
            help="Export results to CSV file (provide path)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        limit = options.get("limit")
        service = options.get("service")
        dry_run = options.get("dry_run", False)
        export_path = options.get("export")

        self.stdout.write(self.style.SUCCESS("🤖 AI Daily Operations Run"))
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("⚠️  DRY RUN MODE - No changes will be made")
            )

        # Run operations
        service = AIOperationsService()
        result = service.run_daily_ops(
            days=days, limit=limit, service=service, dry_run=dry_run
        )

        if result["status"] == "skipped":
            self.stdout.write(
                self.style.WARNING(f"⏭️  Skipped: {result.get('reason', 'Unknown')}")
            )
            return

        if result["status"] == "failed":
            self.stdout.write(
                self.style.ERROR(f"❌ Failed: {result.get('error', 'Unknown error')}")
            )
            return

        # Print summary table
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("📊 Summary"))
        self.stdout.write("-" * 60)

        ai1 = result.get("ai1", {})
        ai2 = result.get("ai2", {})
        ai3 = result.get("ai3", {})

        self.stdout.write(f"Run ID: {result['run_id']}")
        self.stdout.write("")
        self.stdout.write("AI-1 (Meeting Tagging):")
        self.stdout.write(f"  Meetings scanned: {ai1.get('scanned', 0)}")
        self.stdout.write(f"  Created: {ai1.get('created', 0)}")
        self.stdout.write(f"  Cached: {ai1.get('cached', 0)}")
        self.stdout.write(f"  Fallback: {ai1.get('fallback', 0)}")
        self.stdout.write(f"  Errors: {ai1.get('errors', 0)}")

        self.stdout.write("")
        self.stdout.write("AI-3 (Review Suggestions):")
        self.stdout.write(f"  Tasks scanned: {ai3.get('scanned', 0)}")
        self.stdout.write(f"  In review queue: {ai3.get('review_queue_count', 0)}")
        self.stdout.write(f"  Created: {ai3.get('created', 0)}")
        self.stdout.write(f"  Cached: {ai3.get('cached', 0)}")
        self.stdout.write(f"  Fallback: {ai3.get('fallback', 0)}")
        self.stdout.write(f"  Errors: {ai3.get('errors', 0)}")

        self.stdout.write("")
        self.stdout.write("AI-2 (Requirement Checks):")
        self.stdout.write(f"  Tasks scanned: {ai2.get('scanned', 0)}")
        self.stdout.write(f"  Created: {ai2.get('created', 0)}")
        self.stdout.write(f"  Cached: {ai2.get('cached', 0)}")
        self.stdout.write(f"  Fallback: {ai2.get('fallback', 0)}")
        self.stdout.write(f"  Errors: {ai2.get('errors', 0)}")

        # Export to CSV if requested
        if export_path:
            try:
                self._export_to_csv(result, export_path)
                self.stdout.write("")
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Results exported to: {export_path}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error exporting CSV: {e}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✅ AI Daily Operations completed"))

    def _export_to_csv(self, result, export_path):
        """Export run results to CSV"""
        from ai_services.models import AIOperationsRun

        run_id = result.get("run_id")
        if not run_id:
            return

        try:
            run = AIOperationsRun.objects.get(id=run_id)
        except AIOperationsRun.DoesNotExist:
            return

        # Ensure directory exists
        os.makedirs(
            os.path.dirname(export_path) if os.path.dirname(export_path) else ".",
            exist_ok=True,
        )

        with open(export_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(
                [
                    "run_id",
                    "started_at",
                    "finished_at",
                    "status",
                    "days",
                    "limit",
                    "service_name",
                    "dry_run",
                    "meetings_scanned",
                    "meetings_tagged_created",
                    "meetings_tagged_cached",
                    "meetings_tagged_fallback",
                    "tasks_scanned",
                    "tasks_review_queue",
                    "ai_reviews_created",
                    "ai_reviews_cached",
                    "ai_reviews_fallback",
                    "requirement_checks_created",
                    "requirement_checks_cached",
                    "requirement_checks_fallback",
                    "errors_count",
                ]
            )

            # Data row
            writer.writerow(
                [
                    run.id,
                    run.started_at.isoformat() if run.started_at else "",
                    run.finished_at.isoformat() if run.finished_at else "",
                    run.status,
                    run.days,
                    run.limit or "",
                    run.service_name or "",
                    run.dry_run,
                    run.meetings_scanned,
                    run.meetings_tagged_created,
                    run.meetings_tagged_cached,
                    run.meetings_tagged_fallback,
                    run.tasks_scanned,
                    run.tasks_review_queue,
                    run.ai_reviews_created,
                    run.ai_reviews_cached,
                    run.ai_reviews_fallback,
                    run.requirement_checks_created,
                    run.requirement_checks_cached,
                    run.requirement_checks_fallback,
                    run.errors_count,
                ]
            )
