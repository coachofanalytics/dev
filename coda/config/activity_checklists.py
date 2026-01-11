"""
Activity Checklist & Evidence Configuration.

This module defines checklist requirements, minimum durations, and evidence requirements
for meeting-based activities. Used by ChecklistEvaluationService to validate task completion.

Each activity can specify:
- Minimum duration (in minutes) required for the activity
- Required evidence types (e.g., "recording", "summary", "notes")
- Impact tier (high/medium/low) for quality scoring and promotion weighting
- Promotion weight multiplier (higher for high-impact activities)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Impact tiers for activity classification
IMPACT_HIGH = "high"
IMPACT_MEDIUM = "medium"
IMPACT_LOW = "low"


@dataclass
class ChecklistItemConfig:
    """Configuration for a single checklist item."""

    code: str  # Unique identifier (e.g., "REQ_CLARIFICATION")
    label: str  # Human-readable label
    weight: float = 1.0  # Weight for scoring (default 1.0)
    requires_evidence: bool = False  # Whether this item requires evidence


@dataclass
class ActivityChecklistConfig:
    """Configuration for an activity's checklist and evidence requirements."""

    activity_slug: str  # Must match ActivityType.slug
    impact: str = IMPACT_MEDIUM  # high, medium, or low
    required_evidence: List[str] = (
        None  # List of evidence types: ["recording", "summary", ...]
    )
    min_duration_minutes: Optional[int] = (
        None  # Minimum duration required (None = no minimum)
    )
    promotion_weight: float = 1.0  # Weight for promotion/career progression
    primary_evidence_type: Optional[str] = (
        None  # Primary evidence type (e.g., "recording")
    )

    def __post_init__(self):
        if self.required_evidence is None:
            self.required_evidence = []


# Configuration registry for meeting-based activities
ACTIVITY_CHECKLIST_CONFIG: Dict[str, ActivityChecklistConfig] = {
    "PRODUCT_BACKLOG_REFINEMENT": ActivityChecklistConfig(
        activity_slug="PRODUCT_BACKLOG_REFINEMENT",
        impact=IMPACT_HIGH,
        required_evidence=["recording", "summary"],
        min_duration_minutes=120,  # 2 hours minimum
        promotion_weight=2.5,
        primary_evidence_type="recording",
    ),
    "CLIENT_TRAINING_SESSION": ActivityChecklistConfig(
        activity_slug="CLIENT_TRAINING_SESSION",
        impact=IMPACT_HIGH,
        required_evidence=["recording", "summary"],
        min_duration_minutes=120,  # 2 hours minimum
        promotion_weight=2.5,
        primary_evidence_type="recording",
    ),
    "INTERNAL_TRAINING_SESSION": ActivityChecklistConfig(
        activity_slug="INTERNAL_TRAINING_SESSION",
        impact=IMPACT_MEDIUM,
        required_evidence=["recording", "summary"],
        min_duration_minutes=120,  # 2 hours minimum
        promotion_weight=2.0,
        primary_evidence_type="recording",
    ),
    "SELF_TRAINING_SESSION": ActivityChecklistConfig(
        activity_slug="SELF_TRAINING_SESSION",
        impact=IMPACT_MEDIUM,
        required_evidence=["summary"],  # Self-training may not always have recordings
        min_duration_minutes=180,  # 3-4 hours (using 180 minutes as default, configurable)
        promotion_weight=1.5,
        primary_evidence_type="summary",
    ),
    "CLIENT_TRAINING_PREP_SESSION": ActivityChecklistConfig(
        activity_slug="CLIENT_TRAINING_PREP_SESSION",
        impact=IMPACT_HIGH,
        required_evidence=["summary"],  # Prep sessions may have notes/planning docs
        min_duration_minutes=60,  # 1 hour minimum for prep
        promotion_weight=2.0,
        primary_evidence_type="summary",
    ),
    "EMPLOYEE_DAF_REVIEW": ActivityChecklistConfig(
        activity_slug="EMPLOYEE_DAF_REVIEW",
        impact=IMPACT_MEDIUM,
        required_evidence=["summary"],
        min_duration_minutes=60,  # 1 hour minimum
        promotion_weight=1.5,
        primary_evidence_type="summary",
    ),
    # Default fallback for activities not explicitly configured
    "DEFAULT": ActivityChecklistConfig(
        activity_slug="DEFAULT",
        impact=IMPACT_LOW,
        required_evidence=[],  # No specific requirements
        min_duration_minutes=None,  # No minimum duration
        promotion_weight=0.5,
        primary_evidence_type=None,
    ),
}


def get_activity_checklist_config(
    activity_slug: str,
) -> Optional[ActivityChecklistConfig]:
    """
    Get checklist configuration for an activity slug.

    Args:
        activity_slug: ActivityType.slug value

    Returns:
        ActivityChecklistConfig if found, None otherwise
    """
    return ACTIVITY_CHECKLIST_CONFIG.get(
        activity_slug, ACTIVITY_CHECKLIST_CONFIG.get("DEFAULT")
    )


def get_min_duration_minutes(activity_slug: str) -> Optional[int]:
    """
    Get minimum duration requirement for an activity.

    Args:
        activity_slug: ActivityType.slug value

    Returns:
        Minimum duration in minutes, or None if no minimum is required
    """
    config = get_activity_checklist_config(activity_slug)
    return config.min_duration_minutes if config else None


def get_required_evidence(activity_slug: str) -> List[str]:
    """
    Get list of required evidence types for an activity.

    Args:
        activity_slug: ActivityType.slug value

    Returns:
        List of required evidence type strings (e.g., ["recording", "summary"])
    """
    config = get_activity_checklist_config(activity_slug)
    return config.required_evidence if config else []


def get_promotion_weight(activity_slug: str) -> float:
    """
    Get promotion weight for an activity.

    Args:
        activity_slug: ActivityType.slug value

    Returns:
        Promotion weight multiplier (default 0.5 for unconfigured activities)
    """
    config = get_activity_checklist_config(activity_slug)
    return config.promotion_weight if config else 0.5


def get_impact_tier(activity_slug: str) -> str:
    """
    Get impact tier for an activity.

    Args:
        activity_slug: ActivityType.slug value

    Returns:
        Impact tier: "high", "medium", or "low"
    """
    config = get_activity_checklist_config(activity_slug)
    return config.impact if config else IMPACT_LOW


def get_primary_evidence_type(activity_slug: str) -> Optional[str]:
    """
    Get primary evidence type for an activity.

    Args:
        activity_slug: ActivityType.slug value

    Returns:
        Primary evidence type string (e.g., "recording") or None
    """
    config = get_activity_checklist_config(activity_slug)
    return config.primary_evidence_type if config else None
