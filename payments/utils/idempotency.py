from typing import Optional, Dict
from django.utils import timezone
from django.db import transaction
from payments.models import IdempotencyKey


def reserve_idempotency_key(key: str, user=None, ttl_seconds: int = 3600) -> IdempotencyKey:
    """Create or return existing idempotency key record. If existing and used, return it.

    This function is safe to call concurrently; it uses get_or_create and atomic updates.
    """
    expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)
    with transaction.atomic():
        obj, created = IdempotencyKey.objects.select_for_update().get_or_create(key=key, defaults={'created_by': user, 'expires_at': expires_at})
        if not created:
            # Update expires_at if missing
            if obj.expires_at is None:
                obj.expires_at = expires_at
                obj.save()
        return obj


def mark_idempotency_used(key: str, response: Optional[Dict] = None) -> None:
    with transaction.atomic():
        try:
            obj = IdempotencyKey.objects.select_for_update().get(key=key)
            obj.mark_used(response or {})
        except IdempotencyKey.DoesNotExist:
            # create and mark used
            obj = IdempotencyKey.objects.create(key=key, response=response or {}, status='used')
            obj.save()


def get_idempotency_response(key: str) -> Optional[Dict]:
    try:
        obj = IdempotencyKey.objects.get(key=key)
        if obj.status == 'used':
            return obj.response
    except IdempotencyKey.DoesNotExist:
        return None
    return None
