import logging
from typing import Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone

from accounts.models import Credential, CredentialCategory, CustomerUser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed integration credentials from existing environment settings into the credential store."

    def handle(self, *args, **options):
        environment = getattr(settings, "ENVIRONMENT", "local")
        added_by = (
            CustomerUser.objects.filter(is_superuser=True).first()
            or CustomerUser.objects.first()
        )

        if not added_by:
            raise CommandError(
                "No users exist in the system. Create at least one user before seeding credentials."
            )

        # Mapping of integration -> payload extraction callable
        integrations: Dict[str, Dict[str, Any]] = {
            "twilio": {
                "name": "Twilio Messaging",
                "category": "Communications",
                "credential_type": Credential.CredentialType.API,
                "payload": self._twilio_payload(),
                "notes": "Seeded from environment variables via management command.",
            },
            "optionplay": {
                "name": "OptionPlay Data Feed",
                "category": "Market Data",
                "credential_type": Credential.CredentialType.API,
                "payload": self._optionplay_payload(),
                "notes": "Seeded from environment variables via management command.",
            },
            "unusual_whales": {
                "name": "Unusual Whales Flow",
                "category": "Market Data",
                "credential_type": Credential.CredentialType.API,
                "payload": self._unusual_whales_payload(),
                "notes": "Seeded from environment variables via management command.",
            },
        }

        seeded = 0
        for integration, config in integrations.items():
            payload = config["payload"]
            if not payload:
                logger.info(
                    "Skipping %s – no settings found for environment '%s'.",
                    integration,
                    environment,
                )
                continue

            category = self._get_or_create_category(config["category"])

            description = config.get("description") or config.get("notes") or config[
                "name"
            ]

            credential, created = Credential.objects.update_or_create(
                integration_key=integration,
                environment=environment,
                defaults={
                    "name": config["name"],
                    "slug": slugify(f"{integration}-{environment}")[:50],
                    "added_by": added_by,
                    "user_types": "Superuser",
                    "credential_type": config["credential_type"],
                    "is_active": True,
                    "is_featured": True,
                    "notes": config.get("notes", ""),
                    "description": description,
                },
            )

            credential.set_payload(payload)
            credential.rotation_frequency_days = credential.rotation_frequency_days or 0
            if created:
                credential.last_rotated_at = timezone.now()
            credential.save()
            credential.category.set([category] if category else [])

            seeded += 1
            logger.info(
                "%s credential %s for environment '%s'.",
                "Created" if created else "Updated",
                integration,
                environment,
            )

        if not seeded:
            self.stdout.write(
                self.style.WARNING(
                    "No credentials were seeded; ensure environment variables are set."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Seeded {seeded} integration credential(s).")
            )

    # ------------------------------------------------------------------
    # Payload helpers
    # ------------------------------------------------------------------

    def _twilio_payload(self) -> Dict[str, Any]:
        account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "") or ""
        auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "") or ""
        from_number = getattr(settings, "TWILIO_FROM_NUMBER", "") or ""
        whatsapp_from = getattr(settings, "TWILIO_WHATSAPP_FROM", "") or ""
        messaging_service_sid = (
            getattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "") or ""
        )

        payload = {
            "account_sid": account_sid,
            "auth_token": auth_token,
            "sms_from": from_number,
            "whatsapp_from": whatsapp_from,
            "messaging_service_sid": messaging_service_sid,
        }
        # Drop keys with falsy values to avoid storing blanks
        return {k: v for k, v in payload.items() if v}

    def _optionplay_payload(self) -> Dict[str, Any]:
        api_key = getattr(settings, "OPTIONPLAY_API_KEY", "") or ""
        username = getattr(settings, "OPTIONPLAY_USERNAME", "") or ""
        password = getattr(settings, "OPTIONPLAY_PASSWORD", "") or ""

        payload = {
            "api_key": api_key,
            "username": username,
            "password": password,
        }
        return {k: v for k, v in payload.items() if v}

    def _unusual_whales_payload(self) -> Dict[str, Any]:
        api_key = getattr(settings, "UNUSUAL_WHALES_API_KEY", "") or ""
        enabled = getattr(settings, "UNUSUAL_WHALES_ENABLED", False)

        payload = {"api_key": api_key, "enabled": bool(enabled)}
        return {k: v for k, v in payload.items() if v or k == "enabled"}

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _get_or_create_category(self, name: str) -> CredentialCategory | None:
        if not name:
            return None

        category, _ = CredentialCategory.objects.get_or_create(
            category=name,
            defaults={
                "slug": slugify(name),
                "description": name,
                "is_active": True,
                "is_featured": True,
            },
        )
        return category

