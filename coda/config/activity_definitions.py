"""
Activity-level semantic definitions for canonical ActivityTypes.

These definitions describe what each activity really means in practice:
- checklists for what good completion looks like,
- good/bad examples,
- evidence expectations,
- AI context strings for coaching and validation.

They do not affect pay or DAF calculations directly.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

# Import to ensure slugs match catalog
try:
    from coda.config.activity_catalog import CANONICAL_ACTIVITIES
except ImportError:
    CANONICAL_ACTIVITIES = []


@dataclass(frozen=True)
class ActivityDefinition:
    slug: str
    name: str
    checklist: List[str]
    good_examples: List[str]
    bad_examples: List[str]
    evidence_requirements: List[str]
    min_duration_minutes: Optional[int]
    ai_context: str


# Activity definitions dictionary keyed by slug
ACTIVITY_DEFINITIONS: Dict[str, ActivityDefinition] = {
    # Detailed definitions for core activities
    "DAILY_UPDATE_SESSION": ActivityDefinition(
        slug="DAILY_UPDATE_SESSION",
        name="Daily Update Session",
        checklist=[
            "Provide a structured end-of-day update covering what you accomplished today",
            "List any blockers or challenges you encountered",
            "Outline your planned next steps for tomorrow",
            "Keep the update concise and focused (5-10 minutes)",
            "Participate actively in team discussion if it's a group session",
        ],
        good_examples=[
            "Completed Tableau dashboard for client X, blocked on API access, will follow up with IT tomorrow",
            "Finished coding feature Y, identified a minor bug in integration with service Z, will debug first thing tomorrow",
            "Attended client meeting, gathered requirements for new report, next step is to create wireframes",
        ],
        bad_examples=[
            "Did some work today",
            "Worked on stuff, no blockers",
            "Just checking in",
        ],
        evidence_requirements=[
            "Meeting link or attendance confirmation",
            "Brief summary of key points discussed (if applicable)",
        ],
        min_duration_minutes=5,
        ai_context=(
            "Daily Update Session is a structured end-of-day meeting where employees share "
            "what they accomplished, blockers they faced, and next steps. It promotes transparency, "
            "accountability, and helps identify potential issues early. Success involves clear, "
            "concise communication and active participation."
        ),
    ),
    # Add more definitions as needed - for now, we'll have a minimal set
    # that covers the canonical activities. The service will handle missing definitions gracefully.
}

# Helper function to get activity definition by slug
def get_activity_definition(slug: str) -> Optional[ActivityDefinition]:
    """Get activity definition by slug, or None if not found."""
    return ACTIVITY_DEFINITIONS.get(slug)

