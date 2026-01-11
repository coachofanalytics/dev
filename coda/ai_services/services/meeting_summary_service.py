"""
Meeting Summary Service (AI-4 Part B)

AI-powered meeting summaries for autolinked evidence.
Operates in shadow mode only - never blocks or auto-approves.

Feature Flags:
- AI_ENABLED: Master flag (must be True)
- AI_SHADOW_MODE: Always True for this feature (advisory only)
"""

import hashlib
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from ai_services.models import (Meeting, MeetingAttendee,
                                MeetingSummarySuggestion)
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MeetingSummaryService:
    """
    Service for AI-powered meeting summaries.

    Generates structured summaries for meetings that are autolinked to tasks.
    """

    def __init__(self):
        self.ai_enabled = getattr(settings, "AI_ENABLED", False)
        self.ai_service = self._get_ai_service()

        if not self.ai_enabled:
            logger.debug("AI meeting summary disabled")

    def _get_ai_service(self):
        """Get AI service via interface"""
        try:
            from ai_services.ai_integration_service import RealAIService

            return RealAIService()
        except ImportError:
            logger.warning("RealAIService not available, using fallback")
            return None

    def generate_summary(
        self, meeting: Meeting, force: bool = False
    ) -> Optional[MeetingSummarySuggestion]:
        """
        Generate meeting summary for a meeting.

        Args:
            meeting: Meeting instance
            force: If True, bypass cache and create new summary

        Returns:
            MeetingSummarySuggestion instance or None if error
        """
        try:
            # Generate input hash for caching
            input_hash = self._generate_input_hash(meeting)

            # Check cache first (unless force=True)
            if not force:
                cached_summary = self._check_cache(input_hash)
                if cached_summary:
                    logger.debug(f"Cache hit for meeting summary: meeting {meeting.id}")
                    return cached_summary

            # Build context
            context = self._build_context(meeting)

            # Generate summary
            if self.ai_enabled and self.ai_service:
                summary_data = self._call_ai_analysis(context)
            else:
                summary_data = self._rule_based_fallback(context)

            if not summary_data:
                logger.warning(f"Could not generate summary for meeting {meeting.id}")
                return None

            # Create or update suggestion
            summary, created = MeetingSummarySuggestion.objects.update_or_create(
                meeting=meeting,
                input_hash=input_hash,
                defaults={
                    "summary_text": summary_data["summary_text"],
                    "what_this_proves": summary_data["what_this_proves"],
                    "confidence": summary_data.get("confidence", 0.7),
                    "provider": summary_data.get("provider", "fallback"),
                    "model": summary_data.get("model", "rule_based"),
                    "is_active": True,
                },
            )

            logger.info(
                f"{'Created' if created else 'Updated'} meeting summary: "
                f"meeting {meeting.id}"
            )

            return summary

        except Exception as e:
            logger.error(f"Error generating meeting summary: {e}", exc_info=True)
            return None

    def _build_context(self, meeting: Meeting) -> Dict[str, Any]:
        """Build context for meeting summary"""
        context = {
            "meeting_id": meeting.meeting_id,
            "topic": meeting.topic[:500] if meeting.topic else "",
            "start_time": meeting.start_time.isoformat() if meeting.start_time else "",
            "duration_minutes": meeting.duration_minutes or 0,
            "requirement_code": meeting.requirement_code or "",
        }

        # Get attendee info
        attendees = MeetingAttendee.objects.filter(meeting=meeting)
        context["attendee_count"] = attendees.count()
        context["attendee_names"] = [
            a.attendee_name for a in attendees[:10]
        ]  # Limit to 10

        return context

    def _generate_input_hash(self, meeting: Meeting) -> str:
        """Generate hash for cache deduplication"""
        key_parts = [
            str(meeting.id),
            str(meeting.topic or "")[:200],
            str(meeting.requirement_code or ""),
            str(meeting.duration_minutes or 0),
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _check_cache(self, input_hash: str) -> Optional[MeetingSummarySuggestion]:
        """Check if summary is cached"""
        try:
            now = timezone.now()
            cached = (
                MeetingSummarySuggestion.objects.filter(
                    input_hash=input_hash, is_active=True, expires_at__gt=now
                )
                .order_by("-created_at")
                .first()
            )

            return cached
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None

    def _call_ai_analysis(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call AI service to generate summary"""
        if not self.ai_service:
            return self._rule_based_fallback(context)

        try:
            analysis_type = "meeting_summary"
            session_id = f"meeting_{context['meeting_id']}"

            ai_response = self.ai_service.get_prediction(
                analysis_type=analysis_type, input_data=context, session_id=session_id
            )

            return self._parse_ai_response(ai_response, context)

        except Exception as e:
            logger.error(f"AI service call failed: {e}")
            return self._rule_based_fallback(context)

    def _parse_ai_response(
        self, ai_response: Dict[str, Any], context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Parse AI service response"""
        try:
            import json
            import re

            raw_response = ai_response.get("raw_response", "")

            # Try to parse JSON from response
            json_match = re.search(r"\{[^}]+\}", raw_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())

                if "summary_text" in parsed and "what_this_proves" in parsed:
                    return {
                        "summary_text": parsed.get("summary_text", ""),
                        "what_this_proves": parsed.get("what_this_proves", ""),
                        "confidence": float(parsed.get("confidence", 0.7)),
                        "provider": "openai",
                        "model": ai_response.get("model_used", "gpt4_primary"),
                    }

            # Fallback
            return self._rule_based_fallback(context)

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._rule_based_fallback(context)

    def _rule_based_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based summary"""
        topic = context.get("topic", "Meeting")
        duration = context.get("duration_minutes", 0)
        attendee_count = context.get("attendee_count", 0)
        req_code = context.get("requirement_code", "")

        summary_bullets = [
            f"Meeting topic: {topic[:100]}",
            f"Duration: {duration} minutes",
            f"Attendees: {attendee_count}",
        ]

        if req_code:
            summary_bullets.append(f"Requirement: {req_code}")

        summary_text = "\n".join(f"- {bullet}" for bullet in summary_bullets[:8])

        what_this_proves = (
            f"This meeting demonstrates participation in a {duration}-minute session"
        )
        if req_code:
            what_this_proves += f" related to {req_code}"

        return {
            "summary_text": summary_text,
            "what_this_proves": what_this_proves,
            "confidence": 0.5,  # Low confidence for rule-based
            "provider": "fallback",
            "model": "rule_based",
        }
