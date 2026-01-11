"""
AI Insight Service

Provides AI-generated explanations and coaching for Task/Pay/DAF domain.
Following Section 13 of the v2 Master Document - AI Assist Layer.

Hard Rules (Section 13):
- AI may explain and coach only
- AI may never calculate or decide pay, compliance, or promotions
- AI must not modify any numeric values produced by deterministic services

This service is read-only with respect to calculations - it only generates text.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from coda.config.ai_output_schemas import (CareerCoachingOutput,
                                           ComplianceCoachingOutput,
                                           DAFFocusOutput,
                                           PayExplanationOutput,
                                           QualityFeedbackOutput)

from .ai_service_facade import AIServiceFacade

logger = logging.getLogger(__name__)


class AIInsightService:
    """
    Service for generating AI explanations and coaching text.

    This service provides explanations for pay, compliance, and career decisions
    but NEVER performs calculations or modifies numeric values.

    Following Section 13 - AI Assist Layer:
    - A1: Pay explanations (shadow mode)
    - A2: DAF focus & coaching (shadow mode)
    - A3: Career, Quality & Compliance coaching (shadow mode)
    """

    def __init__(self, ai_facade: Optional[AIServiceFacade] = None) -> None:
        """
        Initialize AIInsightService.

        Args:
            ai_facade: Optional AIServiceFacade instance. If None, creates a new one.
        """
        self.logger = logger
        self.ai_facade = ai_facade or AIServiceFacade()

    def generate_pay_explanation(
        self,
        employee,
        pay_breakdown: dict,
        compliance_data: dict,
        career_state: dict,
    ) -> PayExplanationOutput:
        """
        Generate AI explanation for pay breakdown.

        A1 Shadow Mode Implementation (Option A - Template-only):
        - Uses formatted strings with pre-calculated numbers
        - No real AI calls yet (will be upgraded in future)
        - Provides deterministic, testable output

        Args:
            employee: User instance (employee)
            pay_breakdown: Dict with pre-calculated values:
                - earned_total: Decimal (total earned for the month)
                - released_total: Decimal (amount released/unlocked)
                - locked_total: Decimal (amount locked pending compliance)
                - stipend_release: Decimal (stipend amount if applicable)
                - safety_net_topup: Decimal (safety net top-up if applicable)
            compliance_data: Dict with:
                - compliance_rate: float (percentage, e.g., 45.5 for 45.5%)
                - threshold: float (compliance threshold, typically 33.0)
            career_state: Dict with:
                - group: str (A/B/C)
                - current_level_code: str (e.g., "B5")
                - is_tenured: bool

        Returns:
            PayExplanationOutput with text_en, text_sw, and highlights

        Note:
            This method NEVER calculates pay amounts - it only formats pre-calculated values.
            All numeric values come from deterministic services (PayCalculationService, ReleaseEngine).
        """
        try:
            # Extract values from pay_breakdown (all pre-calculated)
            earned_total = float(pay_breakdown.get("earned_total", 0))
            released_total = float(pay_breakdown.get("released_total", 0))
            locked_total = float(pay_breakdown.get("locked_total", 0))
            stipend_release = float(pay_breakdown.get("stipend_release", 0))
            safety_net_topup = float(pay_breakdown.get("safety_net_topup", 0))

            # Extract compliance data (pre-calculated)
            compliance_rate = compliance_data.get("compliance_rate", 0.0)
            threshold = compliance_data.get("threshold", 33.0)
            is_compliant = compliance_rate >= threshold

            # Extract career state
            group = career_state.get("group", "Unknown")
            current_level = career_state.get("current_level_code", "Unknown")
            is_tenured = career_state.get("is_tenured", False)

            # Generate explanation text (A1 Shadow Mode - Template-based)
            # TODO: Future upgrade to full LLM prompt with structured parsing

            # English explanation
            text_en = self._build_english_explanation(
                earned_total,
                released_total,
                locked_total,
                stipend_release,
                safety_net_topup,
                compliance_rate,
                threshold,
                is_compliant,
                group,
                current_level,
                is_tenured,
            )

            # Swahili explanation (simple helper text for Group B)
            text_sw = self._build_swahili_explanation(
                released_total, compliance_rate, group
            )

            # Highlights (2-5 bullet points)
            highlights = self._build_highlights(
                earned_total,
                released_total,
                locked_total,
                compliance_rate,
                is_compliant,
                stipend_release,
            )

            # Create output
            output = PayExplanationOutput(
                text_en=text_en, text_sw=text_sw, highlights=highlights
            )

            # Internal validation (sanity checks)
            self._validate_output(output)

            return output

        except Exception as e:
            self.logger.error(f"Error generating pay explanation: {e}", exc_info=True)
            # Fall back to safe default
            return self._get_default_explanation()

    def _build_english_explanation(
        self,
        earned_total: float,
        released_total: float,
        locked_total: float,
        stipend_release: float,
        safety_net_topup: float,
        compliance_rate: float,
        threshold: float,
        is_compliant: bool,
        group: str,
        current_level: str,
        is_tenured: bool,
    ) -> str:
        """Build English explanation text from pre-calculated values."""
        parts = []

        # Main earnings summary
        parts.append(f"This month you earned {earned_total:,.0f} KES from your work.")

        # Release status
        if is_compliant:
            parts.append(
                f"Because you met the {threshold}% compliance requirement ({compliance_rate:.1f}%), "
                f"you received {released_total:,.0f} KES this month."
            )
        else:
            parts.append(
                f"Your compliance rate is {compliance_rate:.1f}%, which is below the {threshold}% threshold. "
                f"Therefore, {locked_total:,.0f} KES is currently locked until you meet compliance requirements."
            )
            if released_total > 0:
                parts.append(
                    f"You received {released_total:,.0f} KES from previous months' earnings."
                )

        # Stipend (Group B, tenured only)
        if stipend_release > 0:
            parts.append(
                f"As a tenured employee in Group {group}, you received an additional "
                f"{stipend_release:,.0f} KES stipend based on your compliance performance."
            )

        # Safety net (Group B only)
        if safety_net_topup > 0:
            parts.append(
                f"You also received {safety_net_topup:,.0f} KES as a safety net top-up "
                f"to ensure minimum pay for your attendance."
            )

        # Career context
        if group in ["B", "C"]:
            parts.append(
                f"You are currently at level {current_level} in Group {group}."
            )

        return " ".join(parts)

    def _build_swahili_explanation(
        self, released_total: float, compliance_rate: float, group: str
    ) -> str:
        """Build Swahili explanation text (simple helper for Group B)."""
        if group == "B":
            return f"Ulipata {released_total:,.0f} KES mwezi huu kwa kufikia {compliance_rate:.1f}% ya utimilifu."
        else:
            return f"Ulipata {released_total:,.0f} KES mwezi huu."

    def _build_highlights(
        self,
        earned_total: float,
        released_total: float,
        locked_total: float,
        compliance_rate: float,
        is_compliant: bool,
        stipend_release: float,
    ) -> list:
        """Build 2-5 highlight bullet points."""
        highlights = []

        highlights.append(f"Earned: {earned_total:,.0f} KES this month")

        if is_compliant:
            highlights.append(
                f"Released: {released_total:,.0f} KES (compliant at {compliance_rate:.1f}%)"
            )
        else:
            highlights.append(
                f"Locked: {locked_total:,.0f} KES pending compliance (current: {compliance_rate:.1f}%)"
            )

        if released_total > 0:
            highlights.append(f"Available now: {released_total:,.0f} KES")

        if stipend_release > 0:
            highlights.append(f"Stipend: +{stipend_release:,.0f} KES")

        return highlights[:5]  # Limit to 5 highlights

    def _validate_output(self, output: PayExplanationOutput) -> None:
        """
        Internal validator to ensure output fields are non-empty.

        This is a sanity check - PayExplanationOutput.__post_init__ also validates,
        but this provides an extra layer of safety.
        """
        if not output.text_en or not output.text_en.strip():
            raise ValueError("text_en must be non-empty")
        if not output.text_sw or not output.text_sw.strip():
            raise ValueError("text_sw must be non-empty")
        if not output.highlights or len(output.highlights) == 0:
            raise ValueError("highlights must be non-empty")
        if not all(h.strip() for h in output.highlights):
            raise ValueError("all highlights must be non-empty")

    def _get_default_explanation(self) -> PayExplanationOutput:
        """
        Return a safe default explanation if generation fails.

        This ensures we never return invalid output.
        """
        return PayExplanationOutput(
            text_en="Your pay breakdown is being processed. Please check back shortly.",
            text_sw="Uchambuzi wa malipo yako unafanywa. Tafadhali rudi baadaye.",
            highlights=["Processing pay explanation", "Please check back later"],
        )

    def generate_daf_focus(
        self,
        employee,
        career_data: dict,
        money_data: dict,
        metrics_data: dict,
        activities_data: list,
    ) -> DAFFocusOutput:
        """
        Generate AI-driven DAF focus and coaching recommendations.

        A2 Shadow Mode Implementation (Option A - Template-only):
        - Uses heuristics to derive focus areas from pre-calculated data
        - No real AI calls yet (will be upgraded in future)
        - Provides deterministic, testable output

        Args:
            employee: User instance (employee)
            career_data: Dict with pre-calculated career state:
                - group: str (A/B/C)
                - current_level_code: str (e.g., "B5")
                - progress_to_next_level: dict (progress data)
                - blockers: list (promotion blockers if any)
                - is_tenured: bool
            money_data: Dict with pre-calculated money data:
                - earned_total: Decimal
                - released_total: Decimal
                - locked_total: Decimal
                - stipend_release: Decimal
                - safety_net_topup: Decimal
            metrics_data: Dict with pre-calculated metrics:
                - compliance_rate: float (current month)
                - quality_score: float (current month)
                - attendance_rate: float (current month)
                - window_compliance: float (rolling window)
                - window_quality: float (rolling window)
            activities_data: List of activity dicts with:
                - activity_name: str
                - quality_score: float
                - promotion_impact: str (if any)
                - activity_definition: dict (if present)

        Returns:
            DAFFocusOutput with focus_areas, recommendations, swahili_helpers, action_items

        Note:
            This method NEVER calculates pay, compliance, or career levels - it only
            formats pre-calculated values into coaching recommendations.
            All numeric values come from deterministic services.
        """
        try:
            # Extract values from pre-calculated data (never calculate)
            compliance_rate = metrics_data.get("compliance_rate", 0.0)
            quality_score = metrics_data.get("quality_score", 0.0)
            attendance_rate = metrics_data.get("attendance_rate", 0.0)
            window_compliance = metrics_data.get("window_compliance", 0.0)
            window_quality = metrics_data.get("window_quality", 0.0)

            group = career_data.get("group", "Unknown")
            current_level = career_data.get("current_level_code", "Unknown")
            blockers = career_data.get("blockers", [])
            is_tenured = career_data.get("is_tenured", False)

            # Build focus areas (1-3 based on heuristics)
            focus_areas = self._build_focus_areas(
                compliance_rate,
                quality_score,
                attendance_rate,
                blockers,
                group,
                current_level,
            )

            # Build recommendations (short, plain-English sentences)
            recommendations = self._build_recommendations(
                compliance_rate,
                quality_score,
                blockers,
                group,
                current_level,
                activities_data,
            )

            # Build Swahili helpers (parallel lines for Group B/non-technical)
            swahili_helpers = self._build_swahili_helpers(
                compliance_rate, quality_score, group, focus_areas
            )

            # Build action items (structured tasks with priorities)
            action_items = self._build_action_items(
                compliance_rate, quality_score, blockers, group, activities_data
            )

            # Create output
            output = DAFFocusOutput(
                focus_areas=focus_areas,
                recommendations=recommendations,
                swahili_helpers=swahili_helpers,
                action_items=action_items,
            )

            # Validation is handled by dataclass __post_init__
            return output

        except Exception as e:
            self.logger.error(f"Error generating DAF focus: {e}", exc_info=True)
            # Fall back to safe default
            return self._get_default_daf_focus()

    def _build_focus_areas(
        self,
        compliance_rate: float,
        quality_score: float,
        attendance_rate: float,
        blockers: list,
        group: str,
        current_level: str,
    ) -> list:
        """Build 1-3 focus areas based on heuristics."""
        focus_areas = []

        # Compliance-based focus
        if compliance_rate < 33.0:
            focus_areas.append("Improve completion rate before 15th of next month")
        elif compliance_rate < 50.0:
            focus_areas.append("Increase task completion to unlock more earnings")

        # Quality-based focus
        if quality_score < 0.6:
            focus_areas.append("Strengthen evidence & checklist coverage")
        elif quality_score < 0.8 and compliance_rate >= 33.0:
            focus_areas.append(
                "Focus on quality improvements for better promotion eligibility"
            )

        # Promotion blockers
        if blockers:
            blocker_text = ", ".join(blockers[:2])  # Limit to first 2 blockers
            focus_areas.append(f"Clear promotion blockers: {blocker_text}")

        # Default if no specific issues
        if not focus_areas:
            if group in ["B", "C"]:
                focus_areas.append(
                    f"Continue consistent performance at level {current_level}"
                )
            else:
                focus_areas.append("Maintain current performance level")

        return focus_areas[:3]  # Limit to 3 focus areas

    def _build_recommendations(
        self,
        compliance_rate: float,
        quality_score: float,
        blockers: list,
        group: str,
        current_level: str,
        activities_data: list,
    ) -> list:
        """Build short, plain-English recommendation sentences."""
        recommendations = []

        # Compliance recommendations
        if compliance_rate < 33.0:
            recommendations.append(
                f"Aim to complete at least 33% of your assigned tasks this month to unlock earnings."
            )
        elif compliance_rate < 50.0:
            recommendations.append(
                f"You're at {compliance_rate:.1f}% compliance. Reaching 50%+ will improve your release rate."
            )

        # Quality recommendations
        if quality_score < 0.6:
            recommendations.append(
                "Include photos, notes, or meeting links as evidence for your tasks to improve quality scores."
            )
        elif quality_score < 0.8:
            recommendations.append(
                "Continue improving task quality to strengthen promotion eligibility."
            )

        # Activity-specific recommendations
        low_quality_activities = [
            act for act in activities_data if act.get("quality_score", 1.0) < 0.6
        ]
        if low_quality_activities:
            act_names = [
                act.get("activity_name", "task") for act in low_quality_activities[:2]
            ]
            recommendations.append(
                f"Focus on improving evidence quality for: {', '.join(act_names)}."
            )

        # Promotion recommendations
        if blockers:
            recommendations.append(
                f"Address the promotion blockers to progress from level {current_level}."
            )
        elif group in ["B", "C"] and compliance_rate >= 50.0 and quality_score >= 0.7:
            recommendations.append(
                "You're performing well. Continue this pace to move to the next level."
            )

        # Default recommendation
        if not recommendations:
            recommendations.append(
                "Keep up the good work and maintain consistent task completion."
            )

        return recommendations[:5]  # Limit to 5 recommendations

    def _build_swahili_helpers(
        self,
        compliance_rate: float,
        quality_score: float,
        group: str,
        focus_areas: list,
    ) -> list:
        """Build parallel Swahili helper text lines (for Group B/non-technical staff)."""
        helpers = []

        if group == "B":
            # Compliance helper
            if compliance_rate < 33.0:
                helpers.append(
                    "Fanya angalau 33% ya kazi zako mwezi huu ili uweze kupata malipo yako."
                )
            elif compliance_rate < 50.0:
                helpers.append(
                    f"Uko kwenye {compliance_rate:.1f}% ya utimilifu. Endelea kufanya kazi zaidi."
                )

            # Quality helper
            if quality_score < 0.6:
                helpers.append(
                    "Ongeza picha, maelezo, au viungo vya mikutano kama ushuhuda wa kazi zako."
                )

            # General encouragement
            if compliance_rate >= 33.0 and quality_score >= 0.6:
                helpers.append("Endelea kufanya kazi vizuri.")
        else:
            # Minimal helpers for other groups
            helpers.append("Endelea kufanya kazi vizuri.")

        return helpers[:3]  # Limit to 3 helpers

    def _build_action_items(
        self,
        compliance_rate: float,
        quality_score: float,
        blockers: list,
        group: str,
        activities_data: list,
    ) -> list:
        """Build structured action items with priorities."""
        action_items = []

        # Priority 1: Critical compliance issue
        if compliance_rate < 33.0:
            action_items.append(
                {
                    "title": "Complete core tasks this week",
                    "description": f"Focus on completing at least 33% of assigned tasks to meet compliance threshold.",
                    "priority": 1,
                }
            )

        # Priority 2: Quality improvement
        if quality_score < 0.6:
            action_items.append(
                {
                    "title": "Add evidence to recent tasks",
                    "description": "Include photos, notes, or meeting links to improve quality scores.",
                    "priority": 2 if compliance_rate >= 33.0 else 3,
                }
            )

        # Priority 2-3: Address blockers
        if blockers:
            for i, blocker in enumerate(blockers[:2]):  # Limit to 2 blockers
                action_items.append(
                    {
                        "title": f"Address blocker: {blocker}",
                        "description": f"Work on clearing this blocker to enable promotion eligibility.",
                        "priority": 2 + i,
                    }
                )

        # Priority 3: General improvement
        if compliance_rate >= 33.0 and quality_score >= 0.6 and not blockers:
            action_items.append(
                {
                    "title": "Maintain current performance",
                    "description": "Continue consistent task completion and quality.",
                    "priority": 3,
                }
            )

        # Ensure priorities are sorted (1 = highest)
        action_items.sort(key=lambda x: x.get("priority", 99))

        return action_items[:5]  # Limit to 5 action items

    def _get_default_daf_focus(self) -> DAFFocusOutput:
        """
        Return a safe default DAF focus if generation fails.

        This ensures we never return invalid output.
        """
        return DAFFocusOutput(
            focus_areas=["Continue consistent performance"],
            recommendations=["Keep up the good work and maintain task completion."],
            swahili_helpers=["Endelea kufanya kazi vizuri."],
            action_items=[
                {
                    "title": "Review your tasks",
                    "description": "Check your task list and complete assigned activities.",
                    "priority": 1,
                }
            ],
        )

    def generate_career_coaching(
        self,
        employee,
        career_state: dict,
        progress_data: dict,
    ) -> CareerCoachingOutput:
        """
        Generate AI-driven career coaching narrative.

        A3 Shadow Mode Implementation (Option A - Template-only):
        - Uses pre-calculated career state and progress data
        - No real AI calls yet (will be upgraded in future)
        - Provides deterministic, testable output

        Args:
            employee: User instance (employee)
            career_state: Dict with pre-calculated career state:
                - group: str (A/B/C)
                - current_level_code: str (e.g., "B5")
                - is_tenured: bool
            progress_data: Dict with pre-calculated progress:
                - progress_to_next_level: dict (progress data, may include progress_percent)
                - blockers: list (promotion blockers if any)

        Returns:
            CareerCoachingOutput with summary, blockers_explained, next_steps

        Note:
            This method NEVER calculates career levels or promotion decisions - it only
            formats pre-calculated values into coaching text.
            All career data comes from deterministic services (CareerLevelService).
        """
        try:
            # Extract values from pre-calculated data (never calculate)
            group = career_state.get("group", "Unknown")
            current_level = career_state.get("current_level_code", "Unknown")
            is_tenured = career_state.get("is_tenured", False)

            blockers = progress_data.get("blockers", [])
            progress_to_next = progress_data.get("progress_to_next_level", {})
            progress_percent = (
                progress_to_next.get("progress_percent", 0.0)
                if isinstance(progress_to_next, dict)
                else 0.0
            )

            # Build summary ("where you are now")
            summary = self._build_career_summary(
                group, current_level, is_tenured, progress_percent
            )

            # Build blockers explanation
            blockers_explained = self._build_blockers_explanation(
                blockers, current_level
            )

            # Build next steps
            next_steps = self._build_career_next_steps(
                blockers, progress_percent, group, current_level
            )

            # Create output
            output = CareerCoachingOutput(
                summary=summary,
                blockers_explained=blockers_explained,
                next_steps=next_steps,
            )

            return output

        except Exception as e:
            self.logger.error(f"Error generating career coaching: {e}", exc_info=True)
            return self._get_default_career_coaching()

    def _build_career_summary(
        self,
        group: str,
        current_level: str,
        is_tenured: bool,
        progress_percent: float,
    ) -> str:
        """Build career summary narrative."""
        parts = []

        if group in ["A", "B", "C"]:
            parts.append(
                f"You are currently at level {current_level} in Group {group}."
            )
        else:
            parts.append(f"You are currently at level {current_level}.")

        if is_tenured:
            parts.append(
                "You have achieved tenured status, which provides additional benefits."
            )

        if progress_percent > 0:
            parts.append(
                f"You are {progress_percent:.0f}% of the way to the next level."
            )
        else:
            parts.append("Focus on completing tasks and improving quality to progress.")

        return " ".join(parts) if parts else "Continue working on your assigned tasks."

    def _build_blockers_explanation(self, blockers: list, current_level: str) -> str:
        """Build plain-language blockers explanation."""
        if not blockers:
            return f"There are no current blockers preventing your progression from level {current_level}. Keep up the good work!"

        if len(blockers) == 1:
            return f"To progress from level {current_level}, you need to address: {blockers[0]}."

        blocker_text = ", ".join(blockers[:-1]) + f", and {blockers[-1]}"
        return f"To progress from level {current_level}, you need to address: {blocker_text}."

    def _build_career_next_steps(
        self,
        blockers: list,
        progress_percent: float,
        group: str,
        current_level: str,
    ) -> list:
        """Build 2-4 concrete next steps."""
        next_steps = []

        if blockers:
            # Add steps to address blockers
            for blocker in blockers[:2]:  # Limit to 2 blockers
                next_steps.append(f"Work on clearing the blocker: {blocker}")

        if progress_percent > 0 and progress_percent < 100:
            next_steps.append(
                f"Continue building progress toward the next level (currently at {progress_percent:.0f}%)."
            )
        elif progress_percent == 0:
            next_steps.append(
                "Focus on completing assigned tasks with high quality to start building progress."
            )

        if not blockers and progress_percent >= 80:
            next_steps.append(
                "You're close to the next level - maintain consistent performance to achieve promotion."
            )

        # Default step if nothing specific
        if not next_steps:
            next_steps.append("Maintain consistent task completion and quality scores.")
            next_steps.append(
                "Review your performance metrics regularly to identify areas for improvement."
            )

        return next_steps[:4]  # Limit to 4 steps

    def _get_default_career_coaching(self) -> CareerCoachingOutput:
        """Return a safe default career coaching if generation fails."""
        return CareerCoachingOutput(
            summary="Continue working on your assigned tasks and maintaining quality standards.",
            blockers_explained="Keep improving your quality and compliance to progress.",
            next_steps=[
                "Complete assigned tasks on time",
                "Ensure high-quality evidence for all tasks",
                "Maintain consistent compliance rates",
            ],
        )

    def generate_quality_feedback(
        self,
        employee,
        task_or_activity: dict,
        quality_score: float,
        missing_items: list,
    ) -> QualityFeedbackOutput:
        """
        Generate AI-driven quality feedback per activity/task.

        A3 Shadow Mode Implementation (Option A - Template-only):
        - Uses pre-calculated quality score and missing items
        - No real AI calls yet (will be upgraded in future)
        - Provides deterministic, testable output

        Args:
            employee: User instance (employee)
            task_or_activity: Dict with activity/task info:
                - activity_name: str
                - activity_definition: dict (optional, may contain checklist info)
            quality_score: float (0-1 scale, where 1.0 is perfect quality)
            missing_items: list of strings (missing checklist items or evidence types)

        Returns:
            QualityFeedbackOutput with message and missing_items_explained

        Note:
            This method NEVER calculates quality scores - it only formats pre-calculated
            values into feedback text.
            All quality data comes from deterministic services (ChecklistEvaluationService).
        """
        try:
            # Build message based on quality score bands
            message = self._build_quality_message(
                quality_score, task_or_activity.get("activity_name", "task")
            )

            # Build missing items explanation
            missing_items_explained = self._build_missing_items_explanation(
                missing_items, quality_score
            )

            # Create output
            output = QualityFeedbackOutput(
                message=message,
                missing_items_explained=missing_items_explained,
            )

            return output

        except Exception as e:
            self.logger.error(f"Error generating quality feedback: {e}", exc_info=True)
            return self._get_default_quality_feedback()

    def _build_quality_message(self, quality_score: float, activity_name: str) -> str:
        """Build quality feedback message based on score bands."""
        # Normalize quality_score to 0-1 if needed (handle 0-100 scale)
        normalized_score = (
            quality_score if quality_score <= 1.0 else quality_score / 100.0
        )

        if normalized_score >= 0.8:
            return f"Excellent work on {activity_name}! Your evidence and checklist coverage are strong. Keep maintaining this high standard."
        elif normalized_score >= 0.6:
            return f"Good work on {activity_name}. You're close to excellent quality. Consider adding a bit more evidence or completing additional checklist items to improve further."
        elif normalized_score >= 0.4:
            return f"{activity_name} needs improvement. Your current quality score is below the target. Focus on adding missing evidence and completing checklist requirements."
        else:
            return f"{activity_name} requires significant improvement. Your quality score is low. Start by adding basic evidence (photos, notes, or meeting links) and completing the core checklist items."

    def _build_missing_items_explanation(
        self, missing_items: list, quality_score: float
    ) -> list:
        """Build explanation of missing items."""
        missing_explained = []

        if missing_items:
            for item in missing_items:
                if isinstance(item, str) and item.strip():
                    missing_explained.append(f"Missing: {item}")
        elif quality_score < 0.6:
            # Generic suggestions if no specific missing items provided
            missing_explained.append(
                "Consider adding photos or screenshots as evidence"
            )
            missing_explained.append(
                "Include notes or descriptions explaining the work done"
            )
            missing_explained.append("Complete all required checklist items")

        return missing_explained

    def _get_default_quality_feedback(self) -> QualityFeedbackOutput:
        """Return a safe default quality feedback if generation fails."""
        return QualityFeedbackOutput(
            message="Continue working on adding evidence and completing checklist items to improve quality.",
            missing_items_explained=[
                "Add evidence to support your work",
                "Complete all checklist requirements",
            ],
        )

    def generate_compliance_coaching(
        self,
        employee,
        compliance_data: dict,
        target_month: int,
        target_year: int,
    ) -> ComplianceCoachingOutput:
        """
        Generate AI-driven compliance coaching.

        A3 Shadow Mode Implementation (Option A - Template-only):
        - Uses pre-calculated compliance data
        - No real AI calls yet (will be upgraded in future)
        - Provides deterministic, testable output

        Args:
            employee: User instance (employee)
            compliance_data: Dict with pre-calculated compliance:
                - completion_rate: float (percentage, e.g., 24.5 for 24.5%)
                - threshold: float (compliance threshold, typically 33.0)
                - days_to_15th: int (optional, days until 15th of next month)
            target_month: int (1-12)
            target_year: int (YYYY)

        Returns:
            ComplianceCoachingOutput with summary and what_to_do

        Note:
            This method NEVER calculates compliance - it only formats pre-calculated
            values into coaching text.
            All compliance data comes from deterministic services (ComplianceCalculator).
        """
        try:
            # Extract values from pre-calculated data (never calculate)
            completion_rate = compliance_data.get("completion_rate", 0.0)
            threshold = compliance_data.get("threshold", 33.0)
            days_to_15th = compliance_data.get("days_to_15th", None)

            # Month name for readability
            month_names = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
            month_name = (
                month_names[target_month - 1]
                if 1 <= target_month <= 12
                else f"Month {target_month}"
            )

            # Build summary
            summary = f"You are at {completion_rate:.1f}% completion for {month_name} {target_year}."

            # Build what_to_do guidance
            what_to_do = self._build_compliance_guidance(
                completion_rate, threshold, days_to_15th, month_name
            )

            # Create output
            output = ComplianceCoachingOutput(
                summary=summary,
                what_to_do=what_to_do,
            )

            return output

        except Exception as e:
            self.logger.error(
                f"Error generating compliance coaching: {e}", exc_info=True
            )
            return self._get_default_compliance_coaching()

    def _build_compliance_guidance(
        self,
        completion_rate: float,
        threshold: float,
        days_to_15th: Optional[int],
        month_name: str,
    ) -> str:
        """Build compliance guidance based on completion rate."""
        gap = threshold - completion_rate

        if completion_rate >= threshold:
            return f"You've met the {threshold}% compliance threshold for {month_name}. Great work! Continue maintaining this level of completion."

        if gap <= 5.0:
            return f"You're very close to the {threshold}% threshold (only {gap:.1f}% away). Focus on completing a few more tasks this week to unlock your earnings."

        if gap <= 15.0:
            guidance = f"You need to increase your completion rate by {gap:.1f}% to meet the {threshold}% threshold."
            if days_to_15th is not None and days_to_15th > 0:
                guidance += f" You have {days_to_15th} days before the 15th of next month to improve your completion rate."
            return guidance

        # Significant gap
        guidance = f"You need to significantly increase your completion rate (currently {gap:.1f}% below the {threshold}% threshold)."
        if days_to_15th is not None and days_to_15th > 0:
            guidance += f" Start completing tasks now - you have {days_to_15th} days before the cutoff."
        else:
            guidance += " Focus on completing assigned tasks daily to build up your completion rate."

        return guidance

    def _get_default_compliance_coaching(self) -> ComplianceCoachingOutput:
        """Return a safe default compliance coaching if generation fails."""
        return ComplianceCoachingOutput(
            summary="Review your task completion status regularly.",
            what_to_do="Aim to complete at least 33% of your assigned tasks before the 15th of each month to meet compliance requirements.",
        )
