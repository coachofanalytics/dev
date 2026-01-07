"""
Consent Management Service for GDPR compliance.

Manages user consent for data processing:
- Record consent decisions
- Track consent versions
- Withdraw consent
- Query consent status
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from django.contrib.auth.models import User
from django.utils import timezone

from gdpr.models import ConsentRecord, PrivacyPolicyVersion

logger = logging.getLogger(__name__)


class ConsentService:
    """
    Service for managing user consent.

    GDPR Article 7: Conditions for consent
    GDPR Article 13: Information to be provided
    """

    @staticmethod
    def give_consent(
        user: User,
        consent_type: str,
        version: str,
        consent_text: str = "",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        """
        Record user consent.

        Args:
            user: User giving consent
            consent_type: Type of consent (from CONSENT_TYPE_CHOICES)
            version: Version of policy/terms
            consent_text: Full text of what was consented to
            ip_address: IP address when consent was given
            user_agent: Browser user agent

        Returns:
            ConsentRecord: Created or updated consent record
        """
        # Get or create consent record
        consent, created = ConsentRecord.objects.get_or_create(
            user=user,
            consent_type=consent_type,
            defaults={
                "version": version,
                "consent_text": consent_text,
            }
        )

        # If updating existing record
        if not created:
            consent.version = version
            consent.consent_text = consent_text

        # Record consent
        consent.give_consent(ip_address=ip_address, user_agent=user_agent)

        action = "Created" if created else "Updated"
        logger.info(
            f"{action} consent record for user {user.username}: "
            f"{consent_type} v{version}"
        )

        return consent

    @staticmethod
    def withdraw_consent(
        user: User,
        consent_type: str,
    ) -> Optional[ConsentRecord]:
        """
        Withdraw user consent.

        Args:
            user: User withdrawing consent
            consent_type: Type of consent to withdraw

        Returns:
            ConsentRecord if found and withdrawn, None otherwise
        """
        try:
            consent = ConsentRecord.objects.get(
                user=user,
                consent_type=consent_type,
                is_given=True,
            )

            consent.withdraw_consent()

            logger.info(
                f"Withdrew consent for user {user.username}: {consent_type}"
            )

            return consent

        except ConsentRecord.DoesNotExist:
            logger.warning(
                f"No active consent found for user {user.username}: {consent_type}"
            )
            return None

    @staticmethod
    def has_consent(
        user: User,
        consent_type: str,
    ) -> bool:
        """
        Check if user has given consent.

        Args:
            user: User to check
            consent_type: Type of consent

        Returns:
            True if user has given consent
        """
        return ConsentRecord.objects.filter(
            user=user,
            consent_type=consent_type,
            is_given=True,
        ).exists()

    @staticmethod
    def get_consent_record(
        user: User,
        consent_type: str,
    ) -> Optional[ConsentRecord]:
        """
        Get consent record for user.

        Args:
            user: User to get consent for
            consent_type: Type of consent

        Returns:
            ConsentRecord if exists, None otherwise
        """
        try:
            return ConsentRecord.objects.get(
                user=user,
                consent_type=consent_type,
            )
        except ConsentRecord.DoesNotExist:
            return None

    @staticmethod
    def get_all_consents(user: User) -> List[ConsentRecord]:
        """
        Get all consent records for user.

        Args:
            user: User to get consents for

        Returns:
            List of ConsentRecord objects
        """
        return list(ConsentRecord.objects.filter(user=user).order_by("-created_at"))

    @staticmethod
    def get_consent_summary(user: User) -> Dict[str, bool]:
        """
        Get summary of all consent types and their status.

        Args:
            user: User to get summary for

        Returns:
            Dictionary mapping consent types to their status
        """
        consents = ConsentRecord.objects.filter(user=user)

        summary = {}
        for choice in ConsentRecord.CONSENT_TYPE_CHOICES:
            consent_type = choice[0]
            consent = consents.filter(consent_type=consent_type).first()
            summary[consent_type] = consent.is_given if consent else False

        return summary

    @staticmethod
    def check_required_consents(user: User) -> Dict[str, Any]:
        """
        Check if user has given all required consents.

        Args:
            user: User to check

        Returns:
            Dictionary with compliance status
        """
        required_consents = [
            "terms_of_service",
            "privacy_policy",
        ]

        missing = []
        for consent_type in required_consents:
            if not ConsentService.has_consent(user, consent_type):
                missing.append(consent_type)

        return {
            "compliant": len(missing) == 0,
            "missing": missing,
            "required": required_consents,
        }


class PrivacyPolicyService:
    """
    Service for managing privacy policy versions.

    Tracks different versions of privacy policy for consent management.
    """

    @staticmethod
    def create_version(
        version: str,
        title: str,
        content: str,
        summary: str = "",
        effective_date: Optional[datetime] = None,
        created_by: Optional[User] = None,
        is_active: bool = False,
    ) -> PrivacyPolicyVersion:
        """
        Create a new privacy policy version.

        Args:
            version: Version number (e.g., "1.0", "1.1")
            title: Title of policy
            content: Full text of policy
            summary: Summary of changes
            effective_date: When this version becomes effective
            created_by: User who created this version
            is_active: Whether this is the active version

        Returns:
            PrivacyPolicyVersion: Created policy version
        """
        if effective_date is None:
            effective_date = timezone.now()

        policy = PrivacyPolicyVersion.objects.create(
            version=version,
            title=title,
            content=content,
            summary=summary,
            effective_date=effective_date,
            created_by=created_by,
            is_active=is_active,
        )

        logger.info(f"Created privacy policy version {version}")
        return policy

    @staticmethod
    def get_active_version() -> Optional[PrivacyPolicyVersion]:
        """
        Get currently active privacy policy version.

        Returns:
            PrivacyPolicyVersion if exists, None otherwise
        """
        return PrivacyPolicyVersion.objects.filter(is_active=True).first()

    @staticmethod
    def get_all_versions() -> List[PrivacyPolicyVersion]:
        """
        Get all privacy policy versions.

        Returns:
            List of PrivacyPolicyVersion objects
        """
        return list(PrivacyPolicyVersion.objects.all().order_by("-effective_date"))

    @staticmethod
    def activate_version(version: str) -> Optional[PrivacyPolicyVersion]:
        """
        Activate a specific policy version.

        Args:
            version: Version to activate

        Returns:
            PrivacyPolicyVersion if found and activated, None otherwise
        """
        try:
            policy = PrivacyPolicyVersion.objects.get(version=version)
            policy.is_active = True
            policy.save()  # This will deactivate other versions

            logger.info(f"Activated privacy policy version {version}")
            return policy

        except PrivacyPolicyVersion.DoesNotExist:
            logger.error(f"Privacy policy version {version} not found")
            return None

    @staticmethod
    def get_user_accepted_version(user: User) -> Optional[str]:
        """
        Get version of privacy policy user has accepted.

        Args:
            user: User to check

        Returns:
            Version string if user has accepted, None otherwise
        """
        consent = ConsentRecord.objects.filter(
            user=user,
            consent_type="privacy_policy",
            is_given=True,
        ).first()

        return consent.version if consent else None

    @staticmethod
    def needs_new_consent(user: User) -> bool:
        """
        Check if user needs to consent to new policy version.

        Args:
            user: User to check

        Returns:
            True if user needs to consent to new version
        """
        active_version = PrivacyPolicyService.get_active_version()
        if not active_version:
            return False

        user_version = PrivacyPolicyService.get_user_accepted_version(user)
        if not user_version:
            return True

        # Check if user's version matches active version
        return user_version != active_version.version
