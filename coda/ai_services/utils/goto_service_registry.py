"""
GoToMeeting Service Registry

Single source of truth for mapping service_name -> OAuth credentials.
Supports dual-account setup: internal (primary) and external (secondary).

Service names:
- gotomeeting_internal: Primary account (codagrandprojects@gmail.com)
- gotomeeting_external: Secondary account (coachofanalytics@gmail.com)

Environment variables:
- INTERNAL (default):
  - GOTO_OAUTH_CLIENT_ID
  - GOTO_OAUTH_CLIENT_SECRET
- EXTERNAL (fallback):
  - GOTO_OAUTH_CLIENT_ID_EXTERNAL
  - GOTO_OAUTH_CLIENT_SECRET_EXTERNAL
"""

import logging
import os
from typing import List, Optional, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)

# Service name constants
SERVICE_INTERNAL = "gotomeeting_internal"
SERVICE_EXTERNAL = "gotomeeting_external"

# Legacy service name for backward compatibility
SERVICE_LEGACY = "gotomeeting"


def list_goto_services() -> List[str]:
    """
    List available GoToMeeting services.

    Returns services in priority order (internal first, then external).
    Only includes services that have credentials configured.

    Returns:
        List of service names (e.g., ["gotomeeting_internal", "gotomeeting_external"])
    """
    services = []

    # Internal (primary) - required
    if get_oauth_credentials(SERVICE_INTERNAL)[0]:
        services.append(SERVICE_INTERNAL)

    # External (secondary) - optional
    if get_oauth_credentials(SERVICE_EXTERNAL)[0]:
        services.append(SERVICE_EXTERNAL)

    return services


def get_oauth_credentials(service_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get OAuth client_id and client_secret for a service.

    Args:
        service_name: Service name ("gotomeeting_internal" or "gotomeeting_external")
                     Also accepts "gotomeeting" for backward compatibility (maps to internal)

    Returns:
        Tuple of (client_id, client_secret) or (None, None) if not configured

    Rules:
    - gotomeeting_internal: Requires GOTO_OAUTH_CLIENT_ID/SECRET
    - gotomeeting_external: Requires EXT_GOTO_OAUTH_CLIENT_ID/SECRET (if missing, returns None)
    - gotomeeting (legacy): Maps to internal credentials
    """
    # Backward compatibility: map "gotomeeting" to internal
    if service_name == SERVICE_LEGACY:
        service_name = SERVICE_INTERNAL
        logger.debug(
            f"Mapped legacy service_name '{SERVICE_LEGACY}' to '{service_name}'"
        )

    if service_name == SERVICE_INTERNAL:
        # Internal (primary) - use standard env vars
        client_id = getattr(settings, "GOTO_OAUTH_CLIENT_ID", None) or os.getenv(
            "GOTO_OAUTH_CLIENT_ID", ""
        )
        client_secret = getattr(
            settings, "GOTO_OAUTH_CLIENT_SECRET", None
        ) or os.getenv("GOTO_OAUTH_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            logger.warning(
                f"Internal service credentials not configured: client_id={bool(client_id)}, secret={bool(client_secret)}"
            )
            return (None, None)

        return (client_id, client_secret)

    elif service_name == SERVICE_EXTERNAL:
        # External (secondary) - use GOTO_OAUTH_CLIENT_ID_EXTERNAL env vars
        client_id = getattr(
            settings, "GOTO_OAUTH_CLIENT_ID_EXTERNAL", None
        ) or os.getenv("GOTO_OAUTH_CLIENT_ID_EXTERNAL", "")
        client_secret = getattr(
            settings, "GOTO_OAUTH_CLIENT_SECRET_EXTERNAL", None
        ) or os.getenv("GOTO_OAUTH_CLIENT_SECRET_EXTERNAL", "")

        if not client_id or not client_secret:
            # External is optional - return None if not configured
            logger.debug(
                f"External service credentials not configured (optional): client_id={bool(client_id)}, secret={bool(client_secret)}"
            )
            return (None, None)

        return (client_id, client_secret)

    else:
        logger.error(f"Unknown service_name: {service_name}")
        return (None, None)


def is_service_enabled(service_name: str) -> bool:
    """
    Check if a service has credentials configured.

    Args:
        service_name: Service name to check

    Returns:
        True if credentials are configured, False otherwise
    """
    client_id, _ = get_oauth_credentials(service_name)
    return client_id is not None
