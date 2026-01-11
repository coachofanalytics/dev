"""
Policy Resolver Service - Resolves policy rules based on employee group.

This service provides policy resolution for DAF compliance checks.
Policies are based on employee groups (Group A vs Group B) and activity types.

Backward compatible: Returns safe defaults if models/fields are missing.
"""

import logging
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

# Activity types that require requirements (typically Group A only)
REQUIREMENT_REQUIRED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",  # Alternative name for PBR
]

# Activity types that require meetings (default: True for all unless explicitly set False)
MEETING_REQUIRED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",
]


class PolicyConfig:
    """
    Policy configuration object.

    Provides policy-driven compliance rules based on employee group and activity type.
    """

    def __init__(self, group_name: str = "Group B"):
        """
        Initialize policy config.

        Args:
            group_name: Employee group name ('Group A', 'Group B', 'Group C', etc.)
                       Defaults to 'Group B' (per legacy_views.py defaults)
        """
        self.group_name = group_name or "Group B"
        self.quality_threshold = 0.8  # Default quality threshold (80%)
        self.sessions_required = 1  # Default meeting sessions required
        self.required_meeting_count = 1  # Default meeting count required

    def get_evidence_minimum(self, activity_type_slug: Optional[str] = None) -> int:
        """
        Get minimum evidence count required for activity type.

        Args:
            activity_type_slug: Optional activity type slug

        Returns:
            Minimum evidence count (default: 1)
        """
        # Default minimum is 1 evidence item
        # Can be extended to return different minimums per activity type if needed
        return 1

    def requires_requirement(self, activity_type_slug: Optional[str] = None) -> bool:
        """
        Check if activity type requires a requirement link.

        Group A: Requires requirements for specific activity types.
        Group B: Does not require requirements (per comment in legacy_views.py).

        Args:
            activity_type_slug: Optional activity type slug

        Returns:
            True if requirement is required, False otherwise
        """
        # Group B does not require requirements (per legacy_views.py comment)
        if self.group_name and "Group B" in self.group_name:
            return False

        # Group A: Require requirements only for specific activity types
        if activity_type_slug and activity_type_slug.upper() in [
            a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
        ]:
            return True

        return False

    def requires_meeting(self, activity_type_slug: Optional[str] = None) -> bool:
        """
        Check if activity type requires meeting evidence.

        Default: True (meetings required) unless explicitly set False by policy.
        Only returns False if policy explicitly opts out (meeting_required=False).

        Args:
            activity_type_slug: Optional activity type slug

        Returns:
            True if meeting is required (default), False if explicitly opted out
        """
        # Default: meetings required for all activities
        # Can be extended to check activity-specific rules if needed
        # For now, default to True (per requirement: "keep meeting default = True unless policy explicitly opts out")
        return True

    def get_duration_minimum(
        self, activity_type_slug: Optional[str] = None
    ) -> Optional[int]:
        """
        Get minimum duration in minutes required for activity type.

        Args:
            activity_type_slug: Optional activity type slug

        Returns:
            Minimum duration in minutes, or None if no minimum specified
        """
        # Default: no duration minimum (None)
        # Can be extended to return activity-specific minimums if needed
        return None


class PolicyResolver:
    """
    Policy resolver for employee groups.

    Resolves policy configuration based on user's group (Group A vs Group B).
    """

    @classmethod
    def for_user(cls, user) -> PolicyConfig:
        """
        Resolve policy for a user based on their group.

        Args:
            user: User instance (auth.User or CustomerUser)

        Returns:
            PolicyConfig instance with group-specific rules

        Raises:
            None - always returns a valid PolicyConfig (backward compatible)
        """
        if not user:
            logger.warning(
                "PolicyResolver.for_user: user is None, using default Group B policy"
            )
            return PolicyConfig(group_name="Group B")

        group_name = None

        # Try to get group from Task.group or Task.groupname (if user has tasks)
        # Priority: UserProfile.career_group > Task.group (most recent) > Task.groupname > default
        try:
            # Check if UserProfile has career_group field (may not exist in all environments)
            if hasattr(user, "profile") and hasattr(user.profile, "career_group"):
                career_group = getattr(user.profile, "career_group", None)
                if career_group:
                    # career_group is a ForeignKey to TaskGroups, get the title
                    group_name = getattr(career_group, "title", None)
                    if group_name:
                        logger.debug(
                            f"PolicyResolver.for_user: Resolved group from career_group: {group_name}"
                        )
                        return PolicyConfig(group_name=group_name)
        except Exception as e:
            logger.debug(
                f"PolicyResolver.for_user: Could not get group from career_group: {e}"
            )

        # Fallback: Check most recent Task.group for this user
        try:
            from management.models import Task

            recent_task = (
                Task.objects.filter(employee=user, is_active=True)
                .order_by("-id")
                .first()
            )
            if recent_task:
                # Priority 1: Task.group (CharField, e.g., "Group A")
                if hasattr(recent_task, "group") and recent_task.group:
                    group_name = recent_task.group
                    logger.debug(
                        f"PolicyResolver.for_user: Resolved group from Task.group: {group_name}"
                    )
                    return PolicyConfig(group_name=group_name)

                # Priority 2: Task.groupname (ForeignKey to TaskGroups)
                if hasattr(recent_task, "groupname") and recent_task.groupname:
                    group_name = getattr(recent_task.groupname, "title", None)
                    if group_name:
                        logger.debug(
                            f"PolicyResolver.for_user: Resolved group from Task.groupname: {group_name}"
                        )
                        return PolicyConfig(group_name=group_name)
        except Exception as e:
            logger.debug(f"PolicyResolver.for_user: Could not get group from Task: {e}")

        # Fallback: Check TaskGroups directly (if user has a default group)
        try:
            from accounts.models import TaskGroups

            # Try to get default TaskGroups (ID=1 is often default)
            default_group = TaskGroups.objects.filter(id=1).first()
            if default_group:
                group_name = getattr(default_group, "title", None)
                if group_name:
                    logger.debug(
                        f"PolicyResolver.for_user: Resolved group from default TaskGroups: {group_name}"
                    )
                    return PolicyConfig(group_name=group_name)
        except Exception as e:
            logger.debug(
                f"PolicyResolver.for_user: Could not get group from TaskGroups: {e}"
            )

        # Ultimate fallback: Default to Group B (per legacy_views.py defaults)
        logger.debug(
            f"PolicyResolver.for_user: Using default Group B policy for user {user.username if hasattr(user, 'username') else 'unknown'}"
        )
        return PolicyConfig(group_name="Group B")
