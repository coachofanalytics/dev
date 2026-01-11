"""
AI Output Schemas

Data contracts for AI-generated output in the Task/Pay/DAF domain.
These schemas define the structure of AI explanations and coaching text.

Following Section 13 of the v2 Master Document - AI Assist Layer.
All schemas are read-only data contracts (no Django imports, no side effects).
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class PayExplanationOutput:
    """
    Schema for AI-generated pay explanations.

    This is a data contract only - no AI calls, no Django dependencies.
    Used by AIInsightService.generate_pay_explanation() to structure output.

    Following Section 13.3.1 of the v2 Master Document.

    Attributes:
        text_en: English explanation text (main explanation)
        text_sw: Swahili explanation text (localized helper text)
        highlights: List of 2-5 short bullet points summarizing key points
    """

    text_en: str
    text_sw: str
    highlights: List[str]

    def __post_init__(self):
        """Validate that fields are non-empty."""
        if (
            not self.text_en
            or not isinstance(self.text_en, str)
            or not self.text_en.strip()
        ):
            raise ValueError("text_en must be a non-empty string")
        if (
            not self.text_sw
            or not isinstance(self.text_sw, str)
            or not self.text_sw.strip()
        ):
            raise ValueError("text_sw must be a non-empty string")
        if (
            not self.highlights
            or not isinstance(self.highlights, list)
            or len(self.highlights) == 0
        ):
            raise ValueError("highlights must be a non-empty list")
        if not all(isinstance(h, str) and h.strip() for h in self.highlights):
            raise ValueError("all highlights must be non-empty strings")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text_en": self.text_en,
            "text_sw": self.text_sw,
            "highlights": self.highlights,
        }


@dataclass(frozen=True)
class DAFFocusOutput:
    """
    Schema for AI-generated DAF focus and coaching recommendations.

    This is a data contract only - no AI calls, no Django dependencies.
    Used by AIInsightService.generate_daf_focus() to structure output.

    Following Section 13.3.2 of the v2 Master Document - A2: DAF focus & coaching.

    Attributes:
        focus_areas: List of 1-3 focus area strings (e.g., "Improve completion rate")
        recommendations: List of short, plain-English recommendation sentences
        swahili_helpers: List of parallel Swahili helper text lines for Group B/non-technical staff
        action_items: List of structured action items with title, description, priority
    """

    focus_areas: List[str]
    recommendations: List[str]
    swahili_helpers: List[str]
    action_items: List[Dict[str, Any]]

    def __post_init__(self):
        """Validate that fields are present and types are correct."""
        # Validate focus_areas
        if not isinstance(self.focus_areas, list):
            raise ValueError("focus_areas must be a list")

        # Validate recommendations
        if not isinstance(self.recommendations, list):
            raise ValueError("recommendations must be a list")

        # Validate swahili_helpers
        if not isinstance(self.swahili_helpers, list):
            raise ValueError("swahili_helpers must be a list")

        # Validate action_items
        if not isinstance(self.action_items, list):
            raise ValueError("action_items must be a list")

        # Validate action item structure
        for i, item in enumerate(self.action_items):
            if not isinstance(item, dict):
                raise ValueError(f"action_items[{i}] must be a dict")
            if (
                "title" not in item
                or not isinstance(item["title"], str)
                or not item["title"].strip()
            ):
                raise ValueError(
                    f"action_items[{i}] must have a non-empty 'title' string"
                )
            if (
                "description" not in item
                or not isinstance(item["description"], str)
                or not item["description"].strip()
            ):
                raise ValueError(
                    f"action_items[{i}] must have a non-empty 'description' string"
                )
            if "priority" in item:
                if not isinstance(item["priority"], int) or item["priority"] < 1:
                    raise ValueError(
                        f"action_items[{i}]['priority'] must be a positive integer"
                    )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "focus_areas": self.focus_areas,
            "recommendations": self.recommendations,
            "swahili_helpers": self.swahili_helpers,
            "action_items": self.action_items,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DAFFocusOutput":
        """
        Create DAFFocusOutput from dictionary.

        Args:
            data: Dictionary with focus_areas, recommendations, swahili_helpers, action_items

        Returns:
            DAFFocusOutput instance
        """
        return cls(
            focus_areas=data.get("focus_areas", []),
            recommendations=data.get("recommendations", []),
            swahili_helpers=data.get("swahili_helpers", []),
            action_items=data.get("action_items", []),
        )


@dataclass(frozen=True)
class CareerCoachingOutput:
    """
    Schema for AI-generated career coaching.

    This is a data contract only - no AI calls, no Django dependencies.
    Used by AIInsightService.generate_career_coaching() to structure output.

    Following Section 13.3.3 of the v2 Master Document - A3: Career coaching.

    Attributes:
        summary: High-level narrative about where the employee is (group, level)
        blockers_explained: Plain-language explanation of blockers
        next_steps: List of 2-4 concrete actions for the next 1-3 months
    """

    summary: str
    blockers_explained: str
    next_steps: List[str]

    def __post_init__(self):
        """Validate that fields are non-empty."""
        if (
            not self.summary
            or not isinstance(self.summary, str)
            or not self.summary.strip()
        ):
            raise ValueError("summary must be a non-empty string")
        if (
            not self.blockers_explained
            or not isinstance(self.blockers_explained, str)
            or not self.blockers_explained.strip()
        ):
            raise ValueError("blockers_explained must be a non-empty string")
        if not isinstance(self.next_steps, list):
            raise ValueError("next_steps must be a list")
        if len(self.next_steps) == 0:
            raise ValueError("next_steps must be a non-empty list")
        if not all(isinstance(step, str) and step.strip() for step in self.next_steps):
            raise ValueError("all next_steps must be non-empty strings")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": self.summary,
            "blockers_explained": self.blockers_explained,
            "next_steps": self.next_steps,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CareerCoachingOutput":
        """
        Create CareerCoachingOutput from dictionary.

        Args:
            data: Dictionary with summary, blockers_explained, next_steps

        Returns:
            CareerCoachingOutput instance
        """
        return cls(
            summary=data.get("summary", ""),
            blockers_explained=data.get("blockers_explained", ""),
            next_steps=data.get("next_steps", []),
        )


@dataclass(frozen=True)
class QualityFeedbackOutput:
    """
    Schema for AI-generated quality feedback per activity/task.

    This is a data contract only - no AI calls, no Django dependencies.
    Used by AIInsightService.generate_quality_feedback() to structure output.

    Following Section 13.3.4 of the v2 Master Document - A3: Quality feedback.

    Attributes:
        message: Main feedback message (praise, improvement suggestions, etc.)
        missing_items_explained: List of missing evidence items explained in plain language
    """

    message: str
    missing_items_explained: List[str]

    def __post_init__(self):
        """Validate that fields are present and types are correct."""
        if (
            not self.message
            or not isinstance(self.message, str)
            or not self.message.strip()
        ):
            raise ValueError("message must be a non-empty string")
        if not isinstance(self.missing_items_explained, list):
            raise ValueError("missing_items_explained must be a list")
        if not all(isinstance(item, str) for item in self.missing_items_explained):
            raise ValueError("all missing_items_explained must be strings")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "message": self.message,
            "missing_items_explained": self.missing_items_explained,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QualityFeedbackOutput":
        """
        Create QualityFeedbackOutput from dictionary.

        Args:
            data: Dictionary with message, missing_items_explained

        Returns:
            QualityFeedbackOutput instance
        """
        return cls(
            message=data.get("message", ""),
            missing_items_explained=data.get("missing_items_explained", []),
        )


@dataclass(frozen=True)
class ComplianceCoachingOutput:
    """
    Schema for AI-generated compliance coaching.

    This is a data contract only - no AI calls, no Django dependencies.
    Used by AIInsightService.generate_compliance_coaching() to structure output.

    Following Section 13.3.5 of the v2 Master Document - A3: Compliance coaching.

    Attributes:
        summary: Summary of current compliance status (e.g., "You are at 24% completion for December")
        what_to_do: Plain-language next steps to improve compliance
    """

    summary: str
    what_to_do: str

    def __post_init__(self):
        """Validate that fields are non-empty."""
        if (
            not self.summary
            or not isinstance(self.summary, str)
            or not self.summary.strip()
        ):
            raise ValueError("summary must be a non-empty string")
        if (
            not self.what_to_do
            or not isinstance(self.what_to_do, str)
            or not self.what_to_do.strip()
        ):
            raise ValueError("what_to_do must be a non-empty string")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": self.summary,
            "what_to_do": self.what_to_do,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComplianceCoachingOutput":
        """
        Create ComplianceCoachingOutput from dictionary.

        Args:
            data: Dictionary with summary, what_to_do

        Returns:
            ComplianceCoachingOutput instance
        """
        return cls(
            summary=data.get("summary", ""),
            what_to_do=data.get("what_to_do", ""),
        )
