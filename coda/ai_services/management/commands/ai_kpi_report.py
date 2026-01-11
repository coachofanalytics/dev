"""
Management command to generate AI KPI report.

Generates CSV report with coverage metrics, confidence distributions,
and failure analysis for AI-1, AI-2, and AI-3.
"""

import csv
from collections import Counter
from datetime import timedelta

from ai_services.models import (AIOperationsRun, Meeting,
                                MeetingActivityTagSuggestion)
from django.core.management.base import BaseCommand
from django.utils import timezone
from management.models import (RequirementMatchCheck, Task,
                               TaskAIReviewSuggestion)


class Command(BaseCommand):
    help = "Generate AI KPI report (coverage, confidence, failures)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to analyze (default: 30)",
        )
        parser.add_argument(
            "--export",
            type=str,
            required=True,
            help="Export path for CSV file (required)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        export_path = options["export"]

        self.stdout.write(self.style.SUCCESS("📊 AI KPI Report"))
        self.stdout.write("=" * 60)

        cutoff_date = timezone.now() - timedelta(days=days)

        # Calculate metrics
        metrics = self._calculate_metrics(cutoff_date, days)

        # Print summary
        self._print_summary(metrics, days)

        # Export to CSV
        try:
            self._export_to_csv(metrics, export_path, days)
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(f"✅ Report exported to: {export_path}")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error exporting CSV: {e}"))
            raise

    def _calculate_metrics(self, cutoff_date, days):
        """Calculate all KPI metrics"""
        metrics = {
            "date_range": {
                "start": cutoff_date.date().isoformat(),
                "end": timezone.now().date().isoformat(),
                "days": days,
            }
        }

        # AI-1: Meeting Tagging Coverage
        total_meetings = Meeting.objects.filter(start_time__gte=cutoff_date).count()
        tagged_meetings = (
            MeetingActivityTagSuggestion.objects.filter(
                meeting__start_time__gte=cutoff_date, is_active=True
            )
            .values("meeting")
            .distinct()
            .count()
        )

        metrics["ai1"] = {
            "total_meetings": total_meetings,
            "tagged_meetings": tagged_meetings,
            "coverage_pct": (
                (tagged_meetings / total_meetings * 100) if total_meetings > 0 else 0.0
            ),
        }

        # AI-1: Confidence distribution
        suggestions = MeetingActivityTagSuggestion.objects.filter(
            meeting__start_time__gte=cutoff_date, is_active=True
        )

        confidences = [s.confidence for s in suggestions if s.confidence is not None]
        metrics["ai1"]["avg_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )
        metrics["ai1"]["confidence_high"] = len([c for c in confidences if c >= 0.8])
        metrics["ai1"]["confidence_medium"] = len(
            [c for c in confidences if 0.5 <= c < 0.8]
        )
        metrics["ai1"]["confidence_low"] = len([c for c in confidences if c < 0.5])

        # AI-3: Review Suggestions Coverage
        tasks_in_queue = Task.objects.filter(
            is_active=True, created_at__gte=cutoff_date
        ).count()

        tasks_with_suggestions = (
            TaskAIReviewSuggestion.objects.filter(
                task__created_at__gte=cutoff_date,
                is_active=True,
                expires_at__gt=timezone.now(),
            )
            .values("task")
            .distinct()
            .count()
        )

        metrics["ai3"] = {
            "tasks_in_queue": tasks_in_queue,
            "tasks_with_suggestions": tasks_with_suggestions,
            "coverage_pct": (
                (tasks_with_suggestions / tasks_in_queue * 100)
                if tasks_in_queue > 0
                else 0.0
            ),
        }

        # AI-2: Requirement Checks Coverage
        tasks_with_requirements = Task.objects.filter(
            is_active=True, requirement__isnull=False, created_at__gte=cutoff_date
        ).count()

        tasks_with_checks = (
            RequirementMatchCheck.objects.filter(task__created_at__gte=cutoff_date)
            .values("task")
            .distinct()
            .count()
        )

        metrics["ai2"] = {
            "tasks_with_requirements": tasks_with_requirements,
            "tasks_with_checks": tasks_with_checks,
            "coverage_pct": (
                (tasks_with_checks / tasks_with_requirements * 100)
                if tasks_with_requirements > 0
                else 0.0
            ),
        }

        # Failure analysis from AIOperationsRun
        recent_runs = AIOperationsRun.objects.filter(
            started_at__gte=cutoff_date
        ).order_by("-started_at")

        all_error_samples = []
        for run in recent_runs:
            if run.error_samples:
                all_error_samples.extend(run.error_samples)

        # Top 10 failure reasons
        error_counter = Counter(all_error_samples)
        metrics["failures"] = {
            "total_runs": recent_runs.count(),
            "failed_runs": recent_runs.filter(
                status=AIOperationsRun.RunStatus.FAILED
            ).count(),
            "partial_runs": recent_runs.filter(
                status=AIOperationsRun.RunStatus.PARTIAL
            ).count(),
            "top_10_errors": error_counter.most_common(10),
        }

        return metrics

    def _print_summary(self, metrics, days):
        """Print summary to console"""
        self.stdout.write("")
        self.stdout.write(
            f"Date Range: {metrics['date_range']['start']} to {metrics['date_range']['end']} ({days} days)"
        )
        self.stdout.write("")

        self.stdout.write("AI-1 (Meeting Tagging):")
        self.stdout.write(f"  Total meetings: {metrics['ai1']['total_meetings']}")
        self.stdout.write(f"  Tagged meetings: {metrics['ai1']['tagged_meetings']}")
        self.stdout.write(f"  Coverage: {metrics['ai1']['coverage_pct']:.1f}%")
        self.stdout.write(f"  Avg confidence: {metrics['ai1']['avg_confidence']:.2f}")
        self.stdout.write(f"  High (>=0.8): {metrics['ai1']['confidence_high']}")
        self.stdout.write(f"  Medium (0.5-0.8): {metrics['ai1']['confidence_medium']}")
        self.stdout.write(f"  Low (<0.5): {metrics['ai1']['confidence_low']}")

        self.stdout.write("")
        self.stdout.write("AI-3 (Review Suggestions):")
        self.stdout.write(f"  Tasks in queue: {metrics['ai3']['tasks_in_queue']}")
        self.stdout.write(
            f"  Tasks with suggestions: {metrics['ai3']['tasks_with_suggestions']}"
        )
        self.stdout.write(f"  Coverage: {metrics['ai3']['coverage_pct']:.1f}%")

        self.stdout.write("")
        self.stdout.write("AI-2 (Requirement Checks):")
        self.stdout.write(
            f"  Tasks with requirements: {metrics['ai2']['tasks_with_requirements']}"
        )
        self.stdout.write(f"  Tasks with checks: {metrics['ai2']['tasks_with_checks']}")
        self.stdout.write(f"  Coverage: {metrics['ai2']['coverage_pct']:.1f}%")

        self.stdout.write("")
        self.stdout.write("Operations Runs:")
        self.stdout.write(f"  Total runs: {metrics['failures']['total_runs']}")
        self.stdout.write(f"  Failed runs: {metrics['failures']['failed_runs']}")
        self.stdout.write(f"  Partial runs: {metrics['failures']['partial_runs']}")

        if metrics["failures"]["top_10_errors"]:
            self.stdout.write("")
            self.stdout.write("Top 10 Failure Reasons:")
            for error, count in metrics["failures"]["top_10_errors"]:
                self.stdout.write(f"  {count}x: {error[:80]}")

    def _export_to_csv(self, metrics, export_path, days):
        """Export metrics to CSV"""
        import os

        # Ensure directory exists
        os.makedirs(
            os.path.dirname(export_path) if os.path.dirname(export_path) else ".",
            exist_ok=True,
        )

        with open(export_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(["metric_category", "metric_name", "value"])

            # Date range
            writer.writerow(
                ["date_range", "start_date", metrics["date_range"]["start"]]
            )
            writer.writerow(["date_range", "end_date", metrics["date_range"]["end"]])
            writer.writerow(["date_range", "days", days])

            # AI-1 metrics
            writer.writerow(["ai1", "total_meetings", metrics["ai1"]["total_meetings"]])
            writer.writerow(
                ["ai1", "tagged_meetings", metrics["ai1"]["tagged_meetings"]]
            )
            writer.writerow(
                ["ai1", "coverage_pct", f"{metrics['ai1']['coverage_pct']:.2f}"]
            )
            writer.writerow(
                ["ai1", "avg_confidence", f"{metrics['ai1']['avg_confidence']:.2f}"]
            )
            writer.writerow(
                ["ai1", "confidence_high", metrics["ai1"]["confidence_high"]]
            )
            writer.writerow(
                ["ai1", "confidence_medium", metrics["ai1"]["confidence_medium"]]
            )
            writer.writerow(["ai1", "confidence_low", metrics["ai1"]["confidence_low"]])

            # AI-3 metrics
            writer.writerow(["ai3", "tasks_in_queue", metrics["ai3"]["tasks_in_queue"]])
            writer.writerow(
                [
                    "ai3",
                    "tasks_with_suggestions",
                    metrics["ai3"]["tasks_with_suggestions"],
                ]
            )
            writer.writerow(
                ["ai3", "coverage_pct", f"{metrics['ai3']['coverage_pct']:.2f}"]
            )

            # AI-2 metrics
            writer.writerow(
                [
                    "ai2",
                    "tasks_with_requirements",
                    metrics["ai2"]["tasks_with_requirements"],
                ]
            )
            writer.writerow(
                ["ai2", "tasks_with_checks", metrics["ai2"]["tasks_with_checks"]]
            )
            writer.writerow(
                ["ai2", "coverage_pct", f"{metrics['ai2']['coverage_pct']:.2f}"]
            )

            # Operations runs
            writer.writerow(
                ["operations", "total_runs", metrics["failures"]["total_runs"]]
            )
            writer.writerow(
                ["operations", "failed_runs", metrics["failures"]["failed_runs"]]
            )
            writer.writerow(
                ["operations", "partial_runs", metrics["failures"]["partial_runs"]]
            )

            # Top 10 errors
            for idx, (error, count) in enumerate(
                metrics["failures"]["top_10_errors"], 1
            ):
                writer.writerow(
                    ["failures", f"top_error_{idx}", f"{count}x: {error[:200]}"]
                )
