"""
AI Status Service

Provides safe, crash-proof access to AI system status for staff dashboard.
Never raises exceptions even if AI tables/models are missing.
"""

import logging
from typing import Any, Dict, Optional

from ai_services.utils.flags import get_all_ai_flags
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AIStatusService:
    """
    Service for retrieving AI system status.

    Designed to never crash even if:
    - ai_services app is not installed
    - AutolinkRun model is missing
    - Database tables don't exist
    - Cache backend doesn't support stats
    """

    def get_status(self, request_user=None) -> Dict[str, Any]:
        """
        Get comprehensive AI system status.

        Args:
            request_user: Optional user object (used for permission checks)

        Returns:
            dict with:
            - flags: dict of all AI feature flags
            - cache: dict with cache backend info and stats
            - last_run: dict with last AutolinkRun stats (if available)
            - errors: list of any errors encountered (for debugging)
        """
        status = {
            "flags": {},
            "cache": {},
            "last_run": {},
            "errors": [],
        }

        # Get feature flags
        try:
            status["flags"] = get_all_ai_flags()
        except Exception as e:
            logger.warning(f"Error getting AI flags: {e}")
            status["errors"].append(f"Flags: {str(e)}")
            status["flags"] = {
                "AI_ENABLED": False,
                "AI_REQUIREMENT_MATCH_ENABLED": False,
                "AI_REVIEW_ASSIST_ENABLED": False,
                "AI_ACTIVITY_TAGGING_ENABLED": False,
                "AI_OPS_ENABLED": False,
                "AI_ANOMALY_DETECT_ENABLED": False,
                "AI_SHADOW_MODE": True,
            }

        # Get cache info
        try:
            cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "Unknown")
            # Extract class name from full path (e.g., 'django.core.cache.backends.locmem.LocMemCache' -> 'LocMemCache')
            cache_backend_name = (
                cache_backend.split(".")[-1] if cache_backend else "Unknown"
            )

            status["cache"] = {
                "backend": cache_backend_name,
                "backend_full": cache_backend,
                "supports_stats": False,  # Most Django cache backends don't expose stats
            }

            # Try to get cache stats (best-effort, may not be supported)
            try:
                # Some cache backends have a _cache attribute with stats
                if hasattr(cache, "_cache"):
                    status["cache"]["supports_stats"] = True
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Error getting cache info: {e}")
            status["errors"].append(f"Cache: {str(e)}")
            status["cache"] = {
                "backend": "Unknown",
                "backend_full": "Unknown",
                "supports_stats": False,
            }

        # Get last run stats (from AutolinkRun if available)
        try:
            from ai_services.models import AutolinkRun

            last_run = AutolinkRun.objects.order_by("-started_at").first()

            if last_run:
                # Calculate duration if we have start/end times
                duration_ms = None
                if hasattr(last_run, "started_at") and hasattr(last_run, "finished_at"):
                    if last_run.started_at and last_run.finished_at:
                        delta = last_run.finished_at - last_run.started_at
                        duration_ms = int(delta.total_seconds() * 1000)

                # Use started_at as created_at (AutolinkRun uses started_at, not created_at)
                created_at = last_run.started_at if last_run.started_at else None

                status["last_run"] = {
                    "exists": True,
                    "created_at": created_at,
                    "status": getattr(last_run, "status", "unknown"),
                    "duration_ms": duration_ms,
                    "linked_count": getattr(
                        last_run, "tasklinks_created", 0
                    ),  # Use tasklinks_created as linked_count
                    "errors_count": getattr(
                        last_run, "tasks_failed", 0
                    ),  # Use tasks_failed as errors_count
                    "tasks_scanned": getattr(
                        last_run, "tasks_scanned", 0
                    ),  # Tasks scanned
                    "tasks_matched": getattr(
                        last_run, "tasks_matched", 0
                    ),  # Tasks matched
                }
            else:
                status["last_run"] = {
                    "exists": False,
                    "message": "No runs recorded yet",
                }

        except ImportError as e:
            logger.debug(f"AutolinkRun model not available: {e}")
            status["last_run"] = {
                "exists": False,
                "message": "AutolinkRun model not available",
            }
        except Exception as e:
            logger.warning(f"Error getting last run stats: {e}")
            status["errors"].append(f"Last run: {str(e)}")
            status["last_run"] = {
                "exists": False,
                "message": f"Error: {str(e)}",
            }

        return status
