"""
Anomaly Detection Service (AI-4 Part A)

AI-powered anomaly detection for tasks to identify potential issues.
Operates in shadow mode only - never blocks or auto-approves.

Feature Flags:
- AI_ENABLED: Master flag (must be True)
- AI_ANOMALY_DETECT_ENABLED: Enable this feature
- AI_SHADOW_MODE: Always True for this feature (advisory only)
"""

import hashlib
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from ai_services.models import Meeting
from django.conf import settings
from django.utils import timezone
from management.models import RequirementMatchCheck, Task, TaskLinks

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """
    Service for AI-powered anomaly detection for tasks.

    Identifies potential issues like:
    - Evidence mismatch with requirement
    - Unusual duration patterns
    - Missing required artifacts
    - Suspicious patterns
    """

    def __init__(self):
        self.ai_enabled = getattr(settings, "AI_ENABLED", False)
        self.feature_enabled = getattr(settings, "AI_ANOMALY_DETECT_ENABLED", False)
        self.shadow_mode = getattr(settings, "AI_SHADOW_MODE", True)
        self.ai_service = self._get_ai_service()

        if not self.ai_enabled or not self.feature_enabled:
            logger.debug("AI anomaly detection disabled")

    def _get_ai_service(self):
        """Get AI service via interface"""
        try:
            from ai_services.ai_integration_service import RealAIService

            return RealAIService()
        except ImportError:
            logger.warning("RealAIService not available, using fallback")
            return None

    def detect_anomalies(
        self, task: Task, force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Detect anomalies for a task.

        Args:
            task: Task instance
            force: If True, bypass cache and create new detection

        Returns:
            Dict with risk_flags, severity, reason, confidence or None if error
        """
        try:
            from ai_services.models import TaskAnomalyFlag

            # Build context
            context = self._build_context(task)

            # Generate input hash for caching
            input_hash = self._generate_input_hash(context)

            # Check cache first (unless force=True)
            if not force:
                cached_flag = self._check_cache(input_hash)
                if cached_flag:
                    logger.debug(f"Cache hit for anomaly detection: task {task.id}")
                    return {
                        "risk_flags": cached_flag.flags_json,
                        "severity": cached_flag.severity,
                        "reason": cached_flag.reason,
                        "confidence": cached_flag.confidence,
                    }

            # Generate detection
            if self.ai_enabled and self.feature_enabled and self.ai_service:
                detection_data = self._call_ai_analysis(context)
            else:
                detection_data = self._rule_based_fallback(context)

            if not detection_data:
                logger.warning(
                    f"Could not generate anomaly detection for task {task.id}"
                )
                return None

            # Create or update flag
            flag, created = TaskAnomalyFlag.objects.update_or_create(
                task=task,
                input_hash=input_hash,
                defaults={
                    "flags_json": detection_data.get("risk_flags", {}),
                    "severity": detection_data.get("severity", "low"),
                    "reason": detection_data.get("reason", ""),
                    "confidence": detection_data.get("confidence", 0.5),
                    "provider": detection_data.get("provider", "fallback"),
                    "model": detection_data.get("model", "rule_based"),
                    "is_active": True,
                },
            )

            logger.info(
                f"{'Created' if created else 'Updated'} anomaly flag: "
                f"task {task.id}, severity {detection_data.get('severity', 'unknown')}"
            )

            return {
                "risk_flags": flag.flags_json,
                "severity": flag.severity,
                "reason": flag.reason,
                "confidence": flag.confidence,
            }

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            return None

    def _build_context(self, task: Task) -> Dict[str, Any]:
        """Build context for anomaly detection"""
        context = {
            "task_id": task.id,
            "activity_name": task.activity_name
            or (task.activity_type.name if task.activity_type else "UNKNOWN"),
            "employee_username": task.employee.username if task.employee else "UNKNOWN",
            "points": float(task.point or 0),
            "max_points": float(task.mxpoint or 0),
        }

        # Requirement info
        if task.requirement:
            context["requirement"] = {
                "id": task.requirement.id,
                "what": task.requirement.what[:200] if task.requirement.what else "",
            }
        else:
            context["requirement"] = None

        # Evidence summary
        task_links = TaskLinks.objects.filter(task=task, is_active=True)
        evidence_urls = []
        has_meeting = False
        meeting_ids = []

        for link in task_links:
            if link.link:
                evidence_urls.append(link.link[:200])
            if getattr(link, "meeting_id", None):
                meeting_ids.append(link.meeting_id)
                has_meeting = True

        context["evidence"] = {
            "count": task_links.count(),
            "urls": evidence_urls[:5],  # Limit to 5
            "has_meeting": has_meeting,
            "meeting_ids": meeting_ids,
        }

        # Latest requirement match check
        if task.requirement:
            try:
                check = (
                    RequirementMatchCheck.objects.filter(
                        task=task, requirement=task.requirement
                    )
                    .order_by("-created_at")
                    .first()
                )

                if check:
                    context["requirement_match"] = {
                        "status": check.status,
                        "confidence": check.confidence,
                    }
            except Exception:
                pass

        return context

    def _generate_input_hash(self, context: Dict[str, Any]) -> str:
        """Generate hash for cache deduplication"""
        key_parts = [
            str(context.get("task_id", "")),
            str(context.get("activity_name", "")),
            (
                str(context.get("requirement", {}).get("id", ""))
                if context.get("requirement")
                else ""
            ),
            str(len(context.get("evidence", {}).get("urls", []))),
            str(context.get("evidence", {}).get("has_meeting", False)),
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _check_cache(self, input_hash: str) -> Optional[Any]:
        """Check if detection is cached"""
        try:
            from ai_services.models import TaskAnomalyFlag
            from django.utils import timezone

            now = timezone.now()
            cached = (
                TaskAnomalyFlag.objects.filter(
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
        """Call AI service to detect anomalies"""
        if not self.ai_service:
            return self._rule_based_fallback(context)

        try:
            analysis_type = "anomaly_detection"
            session_id = f"task_{context['task_id']}"

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

                # Validate required fields
                if "risk_flags" in parsed and "severity" in parsed:
                    return {
                        "risk_flags": parsed.get("risk_flags", {}),
                        "severity": parsed.get("severity", "low"),
                        "reason": parsed.get("reason", ""),
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
        """Fallback rule-based detection"""
        risk_flags = {}
        severity = "low"
        reasons = []

        # Check for missing requirement (if required)
        if not context.get("requirement"):
            activity_name = context.get("activity_name", "").upper()
            if activity_name in [
                "SELF_TRAINING_SESSION",
                "INTERNAL_TRAINING_SESSION",
                "CLIENT_TRAINING_SESSION",
                "PRODUCT_BACKLOG_REFINEMENT",
                "PBR",
            ]:
                risk_flags["missing_requirement"] = True
                reasons.append("Requirement missing for required activity type")
                severity = "medium"

        # Check for evidence mismatch
        evidence_count = context.get("evidence", {}).get("count", 0)
        if evidence_count == 0:
            risk_flags["no_evidence"] = True
            reasons.append("No evidence submitted")
            severity = "high" if severity == "low" else severity

        # Check requirement match status
        req_match = context.get("requirement_match")
        if req_match and req_match.get("status") == "fail":
            risk_flags["requirement_mismatch"] = True
            reasons.append("Requirement mismatch detected")
            severity = "high" if severity != "high" else severity

        if not risk_flags:
            risk_flags["none"] = True

        return {
            "risk_flags": risk_flags,
            "severity": severity,
            "reason": "; ".join(reasons) if reasons else "No anomalies detected",
            "confidence": 0.5,  # Low confidence for rule-based
            "provider": "fallback",
            "model": "rule_based",
        }
