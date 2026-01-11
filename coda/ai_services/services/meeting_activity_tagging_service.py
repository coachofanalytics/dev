"""
Meeting Activity Tagging Service (AI-1)

AI-powered suggestion of canonical activity types for meetings.
Operates in shadow mode only - never blocks or auto-assigns.

Feature Flags:
- AI_ENABLED: Master flag (must be True for AI suggestions)
- AI_SHADOW_MODE: Always True for this feature (advisory only)
"""

import hashlib
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from ai_services.models import (Meeting, MeetingActivityTagSuggestion,
                                MeetingAttendee)
from ai_services.utils.meeting_normalizer import \
    extract_candidate_activity_tags
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MeetingActivityTaggingService:
    """
    Service for AI-powered canonical activity type suggestions for meetings.

    Operates in shadow mode only - suggestions are advisory and never
    automatically applied to tasks or affect payroll/points.
    """

    def __init__(self):
        self.ai_enabled = getattr(settings, "AI_ENABLED", False)
        self.ai_service = self._get_ai_service()

        if not self.ai_enabled:
            logger.debug("AI meeting activity tagging disabled")

    def _get_ai_service(self):
        """Get AI service via interface"""
        try:
            from ai_services.ai_integration_service import RealAIService

            return RealAIService()
        except ImportError:
            logger.warning("RealAIService not available, using fallback")
            return None

    def suggest_activity_type(
        self, meeting: Meeting, force: bool = False
    ) -> Optional[MeetingActivityTagSuggestion]:
        """
        Suggest canonical activity type for a meeting.

        Args:
            meeting: Meeting instance
            force: If True, bypass cache and create new suggestion

        Returns:
            MeetingActivityTagSuggestion instance or None if error
        """
        try:
            # Generate input hash for caching
            input_hash = self._generate_input_hash(meeting)

            # Check cache first (unless force=True)
            if not force:
                cached_suggestion = self._check_cache(input_hash)
                if cached_suggestion:
                    logger.debug(
                        f"Cache hit for meeting activity tag: meeting {meeting.id}"
                    )
                    return cached_suggestion

            # Perform AI analysis or fallback
            if self.ai_enabled and self.ai_service:
                suggestion_data = self._call_ai_analysis(meeting)
            else:
                suggestion_data = self._rule_based_fallback(meeting)

            if not suggestion_data:
                logger.warning(
                    f"Could not generate suggestion for meeting {meeting.id}"
                )
                return None

            # Create or update suggestion
            suggestion, created = MeetingActivityTagSuggestion.objects.update_or_create(
                meeting=meeting,
                input_hash=input_hash,
                defaults={
                    "suggested_activity_type": suggestion_data[
                        "suggested_activity_type"
                    ],
                    "confidence": suggestion_data["confidence"],
                    "reason": suggestion_data["reason"],
                    "provider": suggestion_data.get("provider", "fallback"),
                    "model": suggestion_data.get("model", "rule_based"),
                    "is_active": True,
                },
            )

            logger.info(
                f"{'Created' if created else 'Updated'} activity tag suggestion: "
                f"meeting {meeting.id} → {suggestion.suggested_activity_type} "
                f"({suggestion.confidence:.2f})"
            )

            return suggestion

        except Exception as e:
            logger.error(f"Error in meeting activity tagging: {e}", exc_info=True)
            return None

    def _generate_input_hash(self, meeting: Meeting) -> str:
        """Generate hash for cache deduplication"""
        # Get attendee emails
        attendee_emails = list(
            MeetingAttendee.objects.filter(meeting=meeting)
            .values_list("attendee_email", flat=True)
            .order_by("attendee_email")
        )

        # Get candidate tags
        candidate_tags = extract_candidate_activity_tags(
            meeting.topic_normalized or meeting.topic
        )

        key_parts = [
            str(meeting.id),
            meeting.topic or "",
            meeting.topic_normalized or "",
            meeting.requirement_code or "",
            meeting.service_name or "",
            ",".join(sorted(attendee_emails)),
            ",".join(sorted(candidate_tags)),
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _check_cache(self, input_hash: str) -> Optional[MeetingActivityTagSuggestion]:
        """Check if suggestion is cached in database"""
        try:
            # Check for recent result (within 24 hours)
            cutoff = timezone.now() - timedelta(hours=24)
            cached = (
                MeetingActivityTagSuggestion.objects.filter(
                    input_hash=input_hash, is_active=True, created_at__gte=cutoff
                )
                .order_by("-created_at")
                .first()
            )

            return cached
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None

    def _call_ai_analysis(self, meeting: Meeting) -> Optional[Dict[str, Any]]:
        """Call AI service to analyze meeting and suggest activity type"""
        if not self.ai_service:
            return self._rule_based_fallback(meeting)

        # Get attendee emails
        attendee_emails = list(
            MeetingAttendee.objects.filter(meeting=meeting).values_list(
                "attendee_email", flat=True
            )
        )

        # Get candidate tags
        candidate_tags = extract_candidate_activity_tags(
            meeting.topic_normalized or meeting.topic
        )

        # Build input data
        input_data = {
            "topic": meeting.topic or "",
            "topic_normalized": meeting.topic_normalized or "",
            "requirement_code": meeting.requirement_code or "",
            "service_name": meeting.service_name or "",
            "attendee_emails": attendee_emails[:10],  # Limit to first 10
            "candidate_tags": candidate_tags,
        }

        try:
            # Call AI service
            analysis_type = "activity_tagging"
            session_id = f"meeting_{meeting.id}"

            ai_response = self.ai_service.get_prediction(
                analysis_type=analysis_type,
                input_data=input_data,
                session_id=session_id,
            )

            # Parse response
            return self._parse_ai_response(ai_response, meeting)

        except Exception as e:
            logger.error(f"AI service call failed: {e}")
            return self._rule_based_fallback(meeting)

    def _parse_ai_response(
        self, ai_response: Dict[str, Any], meeting: Meeting
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
                return {
                    "suggested_activity_type": parsed.get(
                        "suggested_activity_type", "UNKNOWN"
                    ),
                    "confidence": float(parsed.get("confidence", 0.5)),
                    "reason": parsed.get("reason", "AI analysis completed"),
                    "provider": "openai",
                    "model": ai_response.get("model_used", "gpt4_primary"),
                }

            # Fallback: try to extract from recommendations
            recommendations = ai_response.get("recommendations", [])
            if recommendations:
                # Use first recommendation as activity type
                activity_type = recommendations[0].upper().replace(" ", "_")
                return {
                    "suggested_activity_type": activity_type,
                    "confidence": float(ai_response.get("confidence_score", 0.7)),
                    "reason": " ".join(recommendations[:2])[:200],
                    "provider": "openai",
                    "model": ai_response.get("model_used", "gpt4_primary"),
                }

            # Default fallback
            return self._rule_based_fallback(meeting)

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._rule_based_fallback(meeting)

    def _rule_based_fallback(self, meeting: Meeting) -> Optional[Dict[str, Any]]:
        """Fallback rule-based suggestion using candidate tags"""
        candidate_tags = extract_candidate_activity_tags(
            meeting.topic_normalized or meeting.topic
        )

        if not candidate_tags:
            return {
                "suggested_activity_type": "UNKNOWN",
                "confidence": 0.3,
                "reason": "No candidate tags found (rule-based fallback)",
                "provider": "fallback",
                "model": "rule_based",
            }

        # Map candidate tags to canonical activity types
        tag_to_activity = {
            "pbr": "PRODUCT_BACKLOG_REFINEMENT",
            "client_training": "CLIENT_TRAINING_SESSION",
            "internal_training": "INTERNAL_TRAINING_SESSION",
            "self_training": "SELF_TRAINING_SESSION",
            "daily_update": "DAILY_UPDATE_SESSION",
        }

        # Use first matching tag
        suggested_type = tag_to_activity.get(
            candidate_tags[0].lower(), candidate_tags[0].upper()
        )

        return {
            "suggested_activity_type": suggested_type,
            "confidence": 0.5,  # Low confidence for rule-based
            "reason": f'Rule-based suggestion from candidate tags: {", ".join(candidate_tags[:3])}',
            "provider": "fallback",
            "model": "rule_based",
        }
