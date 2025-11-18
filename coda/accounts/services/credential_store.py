from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from accounts.models import Credential

logger = logging.getLogger(__name__)


class CredentialStore:
    """
    Lightweight accessor for encrypted credentials stored in the database.

    Usage:
        store = CredentialStore()
        twilio = store.get("twilio")
        account_sid = twilio.get("account_sid")
    """

    CACHE_TTL_SECONDS = 60

    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or getattr(settings, "ENVIRONMENT", "local")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get(
        self,
        integration_key: str,
        environment: Optional[str] = None,
        *,
        fallback_environments: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a decrypted payload for the given integration/environment.
        Falls back to provided environments (e.g. ['prod']) if not found.
        """
        env = environment or self.environment
        cache_key = self._cache_key(integration_key, env)
        payload = cache.get(cache_key)
        if payload is None:
            payload = self._load_payload(integration_key, env)
            cache.set(cache_key, payload, self.CACHE_TTL_SECONDS)

        if payload or not fallback_environments:
            return payload.copy()

        for fallback_env in fallback_environments:
            if fallback_env == env:
                continue
            payload = self.get(
                integration_key,
                environment=fallback_env,
                fallback_environments=None,
            )
            if payload:
                return payload.copy()
        return {}

    def get_value(
        self,
        integration_key: str,
        secret_key: str,
        default: Any = None,
        *,
        environment: Optional[str] = None,
        fallback_environments: Optional[list[str]] = None,
    ) -> Any:
        payload = self.get(
            integration_key,
            environment=environment,
            fallback_environments=fallback_environments,
        )
        return payload.get(secret_key, default)

    def clear_cache(self, integration_key: Optional[str] = None, environments: Optional[list[str]] = None):
        """
        Invalidate cached payloads.
        """
        envs = environments or [
            self.environment,
            "prod",
            "production",
            "uat",
            "staging",
            "local",
        ]

        if integration_key:
            for env in envs:
                cache.delete(self._cache_key(integration_key, env))
            return

        # Clear common combinations when no integration specified
        for env in envs:
            cache.delete(self._cache_key("twilio", env))
            cache.delete(self._cache_key("optionplay", env))
            cache.delete(self._cache_key("unusual_whales", env))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _cache_key(self, integration_key: str, environment: str) -> str:
        return f"credential-store:{integration_key}:{environment}"

    def _load_payload(self, integration_key: str, environment: str) -> Dict[str, Any]:
        if not integration_key:
            return {}

        try:
            credential = (
                Credential.objects.filter(
                    Q(integration_key=integration_key),
                    Q(environment=environment),
                    Q(is_active=True),
                )
                .order_by("-payload_last_updated", "-entry_date")
                .first()
            )
        except Exception:
            logger.exception(
                "Failed to load credential for integration=%s env=%s",
                integration_key,
                environment,
            )
            return {}

        if not credential:
            return {}

        return credential.get_payload()


# Reusable singleton for convenience
credential_store = CredentialStore()

