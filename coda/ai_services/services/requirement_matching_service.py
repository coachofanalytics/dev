"""
AI Requirement Matching Service

Analyzes whether a task's selected requirement matches the task's activity type
and associated meeting data. Provides match confidence and suggestions.

Feature Flag: ENABLE_AI_REQUIREMENT_MATCHING (default: False)
"""

import hashlib
import logging
import time
from datetime import timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Activity types that require requirement enforcement
REQUIREMENT_REQUIRED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",
]


class AIRequirementMatchingService:
    """
    Service for AI-powered requirement matching analysis.

    Analyzes task-requirement-meeting relationships to detect mismatches
    and suggest better requirement matches.
    """

    def __init__(self):
        self.enabled = getattr(settings, "ENABLE_AI_REQUIREMENT_MATCHING", False)
        self.cache_expiry_hours = 24  # Cache results for 24 hours
        self.ai_service = self._get_ai_service()

        if not self.enabled:
            logger.info(
                "AI Requirement Matching is disabled (ENABLE_AI_REQUIREMENT_MATCHING=False)"
            )

    def _get_ai_service(self):
        """Get AI service via interface"""
        try:
            from ai_services.ai_integration_service import RealAIService

            return RealAIService()
        except ImportError:
            logger.warning("RealAIService not available, using fallback")
            return None

    def analyze_task_requirement_match(
        self, task, requirement=None, meeting=None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze whether task's requirement matches activity type and meeting.

        Args:
            task: Task instance (must have activity_type, requirement)
            requirement: Requirement instance (optional, defaults to task.requirement)
            meeting: Meeting instance (optional, will try to find matched meeting)

        Returns:
            Dict with:
            - ai_match_label: 'MATCH', 'MISMATCH', or 'UNKNOWN'
            - ai_confidence: float (0.0-1.0)
            - ai_reason: str (short explanation)
            - ai_suggested_requirement_id: int or None
            - model_used: str
            - processing_time: float
            - from_cache: bool

        Returns None if feature is disabled or task doesn't require requirement.
        """
        if not self.enabled:
            return None

        # Check if task activity type requires requirement
        # Task has both activity_type (ForeignKey) and activity_name (CharField)
        # Check activity_name first, then activity_type.name if available
        activity_name = task.activity_name or (
            task.activity_type.name if task.activity_type else None
        )
        if (
            not activity_name
            or activity_name not in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
        ):
            return None

        # Use provided requirement or task's requirement
        requirement = requirement or task.requirement
        if not requirement:
            # Task has no requirement - this is a mismatch
            return {
                "ai_match_label": "MISMATCH",
                "ai_confidence": 1.0,
                "ai_reason": "Task requires a requirement but none is selected",
                "ai_suggested_requirement_id": None,
                "model_used": "rule_based",
                "processing_time": 0.0,
                "from_cache": False,
            }

        # Try to find matched meeting if not provided
        if not meeting:
            meeting = self._find_matched_meeting(task)

        # Check cache first
        cache_key = self._generate_cache_key(task, requirement, meeting)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for task {task.id} requirement {requirement.id}")
            return cached_result

        # Call AI service
        start_time = time.time()
        try:
            ai_result = self._call_ai_analysis(task, requirement, meeting)
            processing_time = time.time() - start_time

            result = {
                "ai_match_label": ai_result.get("match_label", "UNKNOWN"),
                "ai_confidence": ai_result.get("confidence", 0.5),
                "ai_reason": ai_result.get("reason", "Analysis completed"),
                "ai_suggested_requirement_id": ai_result.get(
                    "suggested_requirement_id"
                ),
                "model_used": ai_result.get("model_used", "gpt4_primary"),
                "processing_time": processing_time,
                "from_cache": False,
            }

            # Save to cache and database
            self._save_result(task, requirement, meeting, result, cache_key)

            return result

        except Exception as e:
            logger.error(f"AI analysis failed for task {task.id}: {e}", exc_info=True)
            # Return safe fallback
            return {
                "ai_match_label": "UNKNOWN",
                "ai_confidence": 0.0,
                "ai_reason": f"Analysis failed: {str(e)[:100]}",
                "ai_suggested_requirement_id": None,
                "model_used": "error",
                "processing_time": time.time() - start_time,
                "from_cache": False,
            }

    def _find_matched_meeting(self, task):
        """Find meeting matched to this task via TaskLinks"""
        try:
            from ai_services.models import Meeting
            from management.models import TaskLinks

            # Find TaskLinks for this task
            task_link = TaskLinks.objects.filter(task=task).first()
            if not task_link:
                return None

            # Find meeting via evidence URL or other matching
            # This is simplified - actual matching logic is in MeetingEvidenceMatcher
            if hasattr(task_link, "evidence_url") and task_link.evidence_url:
                # Try to match by URL
                from ai_services.utils.meeting_normalizer import normalize_url

                normalized_url = normalize_url(task_link.evidence_url)
                meeting = Meeting.objects.filter(
                    meeting_url_normalized=normalized_url
                ).first()
                if meeting:
                    return meeting

            return None
        except Exception as e:
            logger.warning(f"Error finding matched meeting: {e}")
            return None

    def _generate_cache_key(self, task, requirement, meeting):
        """Generate cache key for deduplication"""
        key_parts = [
            str(task.id),
            str(requirement.id) if requirement else "none",
            str(meeting.id) if meeting else "none",
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _check_cache(self, cache_key):
        """Check if result is cached and still valid"""
        try:
            from ai_services.models import AIRequirementMatch

            cached = AIRequirementMatch.objects.filter(
                cache_key=cache_key, expires_at__gte=timezone.now()
            ).first()

            if cached and cached.is_valid():
                return {
                    "ai_match_label": cached.ai_match_label,
                    "ai_confidence": cached.ai_confidence,
                    "ai_reason": cached.ai_reason,
                    "ai_suggested_requirement_id": (
                        cached.ai_suggested_requirement.id
                        if cached.ai_suggested_requirement
                        else None
                    ),
                    "model_used": cached.model_used,
                    "processing_time": cached.processing_time,
                    "from_cache": True,
                }
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    def _call_ai_analysis(self, task, requirement, meeting):
        """Call AI service to analyze requirement match"""
        if not self.ai_service:
            # Fallback to rule-based analysis
            return self._rule_based_analysis(task, requirement, meeting)

        # Build input data for AI
        activity_name = task.activity_name or (
            task.activity_type.name if task.activity_type else "UNKNOWN"
        )
        input_data = {
            "task_activity_type": activity_name,
            "requirement_what": (
                requirement.what[:500] if requirement.what else ""
            ),  # Limit length
            "requirement_category": (
                requirement.category if hasattr(requirement, "category") else ""
            ),
            "meeting_topic": meeting.topic[:200] if meeting and meeting.topic else "",
            "meeting_topic_normalized": (
                meeting.topic_normalized[:200]
                if meeting and meeting.topic_normalized
                else ""
            ),
        }

        # Build prompt
        prompt = self._build_analysis_prompt(task, requirement, meeting, input_data)

        try:
            # Call AI service
            analysis_type = "requirement_matching"
            session_id = f"task_{task.id}_req_{requirement.id}"

            ai_response = self.ai_service.get_prediction(
                analysis_type=analysis_type,
                input_data={"prompt": prompt, **input_data},
                session_id=session_id,
            )

            # Parse AI response
            return self._parse_ai_response(ai_response, requirement)

        except Exception as e:
            logger.error(f"AI service call failed: {e}")
            # Fallback to rule-based
            return self._rule_based_analysis(task, requirement, meeting)

    def _build_analysis_prompt(self, task, requirement, meeting, input_data):
        """Build prompt for AI analysis"""
        activity_name = task.activity_name or (
            task.activity_type.name if task.activity_type else "UNKNOWN"
        )
        prompt = f"""Analyze whether this task's requirement matches the activity type and meeting context.

Task Activity Type: {activity_name}
Requirement Description: {input_data['requirement_what']}
Requirement Category: {input_data['requirement_category']}
"""

        if meeting:
            prompt += f"""Meeting Topic: {input_data['meeting_topic']}
Meeting Topic (Normalized): {input_data['meeting_topic_normalized']}
"""

        prompt += """
Determine if the requirement is a good match for this activity type and meeting.

Respond in JSON format:
{
    "match_label": "MATCH" or "MISMATCH" or "UNKNOWN",
    "confidence": 0.0-1.0,
    "reason": "Brief explanation (1-2 lines)",
    "suggested_requirement_id": null or integer ID if you have a better suggestion
}
"""
        return prompt

    def _parse_ai_response(self, ai_response, requirement):
        """Parse AI service response into structured format"""
        try:
            # AI service returns dict with recommendations, etc.
            # Extract structured data
            raw_response = ai_response.get("raw_response", "")

            # Try to parse JSON from response
            import json
            import re

            # Look for JSON in response
            json_match = re.search(r"\{[^}]+\}", raw_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "match_label": parsed.get("match_label", "UNKNOWN"),
                    "confidence": float(parsed.get("confidence", 0.5)),
                    "reason": parsed.get("reason", "AI analysis completed"),
                    "suggested_requirement_id": parsed.get("suggested_requirement_id"),
                    "model_used": ai_response.get("model_used", "gpt4_primary"),
                }

            # Fallback: parse from recommendations
            recommendations = ai_response.get("recommendations", [])
            if recommendations:
                # Heuristic: if recommendations suggest mismatch, it's a mismatch
                reason_text = " ".join(recommendations[:2])
                if (
                    "mismatch" in reason_text.lower()
                    or "not match" in reason_text.lower()
                ):
                    match_label = "MISMATCH"
                elif "match" in reason_text.lower():
                    match_label = "MATCH"
                else:
                    match_label = "UNKNOWN"

                return {
                    "match_label": match_label,
                    "confidence": float(ai_response.get("confidence_score", 0.7)),
                    "reason": reason_text[:200],
                    "suggested_requirement_id": None,
                    "model_used": ai_response.get("model_used", "gpt4_primary"),
                }

            # Default fallback
            return {
                "match_label": "UNKNOWN",
                "confidence": 0.5,
                "reason": "AI analysis completed but response format unclear",
                "suggested_requirement_id": None,
                "model_used": ai_response.get("model_used", "gpt4_primary"),
            }

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._rule_based_analysis(None, requirement, None)

    def _rule_based_analysis(self, task, requirement, meeting):
        """Fallback rule-based analysis when AI is unavailable"""
        # Simple heuristic: if requirement category matches activity type, it's likely a match
        if not requirement:
            return {
                "match_label": "MISMATCH",
                "confidence": 1.0,
                "reason": "No requirement selected",
                "suggested_requirement_id": None,
                "model_used": "rule_based",
            }

        # Basic keyword matching
        requirement_text = (requirement.what or "").lower()
        activity_name = (
            task.activity_name
            if task
            else (task.activity_type.name if task and task.activity_type else "")
        )
        activity_lower = activity_name.lower() if activity_name else ""

        # Check for common keywords
        if "training" in activity_lower and "training" in requirement_text:
            match_label = "MATCH"
            confidence = 0.7
        elif "backlog" in activity_lower or "pbr" in activity_lower:
            if "backlog" in requirement_text or "requirement" in requirement_text:
                match_label = "MATCH"
                confidence = 0.7
            else:
                match_label = "MISMATCH"
                confidence = 0.6
        else:
            match_label = "UNKNOWN"
            confidence = 0.5

        return {
            "match_label": match_label,
            "confidence": confidence,
            "reason": "Rule-based analysis (AI unavailable)",
            "suggested_requirement_id": None,
            "model_used": "rule_based",
        }

    def _save_result(self, task, requirement, meeting, result, cache_key):
        """Save result to database cache"""
        try:
            from ai_services.models import AIModelTypes, AIRequirementMatch

            expires_at = timezone.now() + timedelta(hours=self.cache_expiry_hours)

            suggested_requirement = None
            if result.get("ai_suggested_requirement_id"):
                try:
                    from management.models import Requirement

                    suggested_requirement = Requirement.objects.get(
                        id=result["ai_suggested_requirement_id"]
                    )
                except Exception:
                    pass

            AIRequirementMatch.objects.update_or_create(
                task=task,
                requirement=requirement,
                meeting=meeting,
                defaults={
                    "ai_match_label": result["ai_match_label"],
                    "ai_confidence": result["ai_confidence"],
                    "ai_reason": result["ai_reason"],
                    "ai_suggested_requirement": suggested_requirement,
                    "model_used": result.get("model_used", AIModelTypes.GPT4_PRIMARY),
                    "processing_time": result["processing_time"],
                    "cache_key": cache_key,
                    "expires_at": expires_at,
                },
            )

            logger.info(f"Saved AI match result for task {task.id}")

        except Exception as e:
            logger.error(f"Failed to save AI match result: {e}", exc_info=True)
