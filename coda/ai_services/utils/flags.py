"""
AI Feature Flag Helper

Provides safe access to AI feature flags with defaults.
All flags default to False (OFF) unless explicitly enabled via environment variables.
"""

from typing import Optional


def ai_flag(name: str, default: bool = False) -> bool:
    """
    Safely read an AI feature flag from Django settings.

    Args:
        name: Name of the flag (e.g., 'AI_ENABLED', 'AI_REVIEW_ASSIST_ENABLED')
        default: Default value if flag is not found (defaults to False for safety)

    Returns:
        bool: Flag value (always False if flag not found or app not installed)

    Examples:
        >>> ai_flag('AI_ENABLED')  # Returns False by default
        >>> ai_flag('AI_REVIEW_ASSIST_ENABLED')  # Returns False by default
    """
    try:
        from django.conf import settings

        return bool(getattr(settings, name, default))
    except (ImportError, AttributeError):
        # If Django is not available or settings don't exist, return default (False)
        return default


def is_ai_enabled() -> bool:
    """Check if AI is enabled (master flag)."""
    return ai_flag("AI_ENABLED", default=False)


def is_ai_feature_enabled(feature_name: str) -> bool:
    """
    Check if a specific AI feature is enabled.

    Requires both AI_ENABLED (master) and feature-specific flag to be True.

    Args:
        feature_name: Feature name (e.g., 'REQUIREMENT_MATCH', 'REVIEW_ASSIST', 'ACTIVITY_TAGGING')

    Returns:
        bool: True only if both master flag and feature flag are enabled
    """
    if not is_ai_enabled():
        return False

    flag_name = f"AI_{feature_name}_ENABLED"
    return ai_flag(flag_name, default=False)


def get_all_ai_flags() -> dict:
    """
    Get all AI feature flags as a dictionary.

    Returns:
        dict: Mapping of flag names to boolean values
    """
    flags = {
        "AI_ENABLED": ai_flag("AI_ENABLED", default=False),
        "AI_REQUIREMENT_MATCH_ENABLED": ai_flag(
            "AI_REQUIREMENT_MATCH_ENABLED", default=False
        ),
        "AI_REVIEW_ASSIST_ENABLED": ai_flag("AI_REVIEW_ASSIST_ENABLED", default=False),
        "AI_ACTIVITY_TAGGING_ENABLED": ai_flag(
            "AI_ACTIVITY_TAGGING_ENABLED", default=False
        ),
        "AI_OPS_ENABLED": ai_flag("AI_OPS_ENABLED", default=False),
        "AI_ANOMALY_DETECT_ENABLED": ai_flag(
            "AI_ANOMALY_DETECT_ENABLED", default=False
        ),
        "AI_SHADOW_MODE": ai_flag(
            "AI_SHADOW_MODE", default=True
        ),  # Default True for safety
    }
    return flags
