from decimal import Decimal
from typing import Dict, Any

from django.core.management.base import BaseCommand

from investing.models import SuggestedPosition
from investing.services.position_scoring_service import PositionScoringService


class Command(BaseCommand):
    help = "Recalculate AI scores for SuggestedPosition records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbol",
            help="Limit to a specific underlying symbol (case-insensitive).",
        )
        parser.add_argument(
            "--status",
            default="pending",
            help='Filter by review status (pending/approved/modified/rejected). Use "all" for every status.',
        )
        parser.add_argument(
            "--source",
            help="Filter by source (optionplay, thinkorswim, manual, unusual_whales).",
        )
        parser.add_argument(
            "--ids",
            nargs="+",
            type=int,
            help="Explicit list of SuggestedPosition IDs to rescore.",
        )

    def handle(self, *args, **options):
        qs = SuggestedPosition.objects.all()

        if options.get("ids"):
            qs = qs.filter(id__in=options["ids"])
        else:
            status = options.get("status")
            if status and status.lower() != "all":
                qs = qs.filter(review_status=status.lower())

            symbol = options.get("symbol")
            if symbol:
                qs = qs.filter(symbol__iexact=symbol.strip())

            source = options.get("source")
            if source:
                qs = qs.filter(source=source.strip())

        total = qs.count()
        if not total:
            self.stdout.write(self.style.WARNING("No SuggestedPosition records matched the filters."))
            return

        scorer = PositionScoringService()
        updated = 0

        self.stdout.write(f"Rescoring {total} SuggestedPosition record(s)...")

        for suggestion in qs.iterator():
            payload = self._build_payload(suggestion)
            try:
                score_result = scorer.score_position(payload)
            except Exception as exc:  # pragma: no cover - safety net
                self.stderr.write(
                    self.style.WARNING(
                        f"⚠️  Skipping {suggestion.symbol} #{suggestion.id}: scoring error {exc}"
                    )
                )
                continue

            try:
                suggestion.ai_score = Decimal(str(score_result.get("score", 0)))
                suggestion.ai_rating = score_result.get("rating")
                suggestion.ai_breakdown = self._serialize_breakdown(score_result.get("breakdown", {}))
                suggestion.ai_recommendation = score_result.get("recommendation", "")
                suggestion.ai_confidence_level = score_result.get("confidence")
                suggestion.save(
                    update_fields=[
                        "ai_score",
                        "ai_rating",
                        "ai_breakdown",
                        "ai_recommendation",
                        "ai_confidence_level",
                        "updated_at",
                    ]
                )
                updated += 1
            except Exception as exc:  # pragma: no cover - safety net
                self.stderr.write(
                    self.style.WARNING(
                        f"⚠️  Failed to persist score for {suggestion.symbol} #{suggestion.id}: {exc}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Rescored {updated}/{total} SuggestedPosition record(s)."))

    def _build_payload(self, suggestion: SuggestedPosition) -> Dict[str, Any]:
        """
        Build the payload expected by PositionScoringService from a SuggestedPosition.
        """
        return {
            "symbol": suggestion.symbol,
            "strategy": suggestion.strategy,
            "premium": suggestion.premium_collected,
            "max_loss": suggestion.max_loss,
            "dte": suggestion.dte,
            "iv_rank": (suggestion.api_response_data or {}).get("iv_rank"),
            "delta": suggestion.position_delta,
            "theta": suggestion.position_theta,
            "volume": (suggestion.api_response_data or {}).get("volume"),
            "open_interest": (suggestion.api_response_data or {}).get("open_interest"),
            "days_to_earnings": (suggestion.api_response_data or {}).get("days_to_earnings"),
        }

    def _serialize_breakdown(self, breakdown: Dict[str, Any]) -> Dict[str, float]:
        """
        Ensure the breakdown dictionary is JSON serializable by converting Decimals to floats.
        """
        safe_breakdown: Dict[str, float] = {}
        for key, value in (breakdown or {}).items():
            try:
                safe_breakdown[key] = float(value)
            except (TypeError, ValueError):
                continue
        return safe_breakdown




