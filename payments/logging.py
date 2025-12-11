import logging
import json

logger = logging.getLogger('payments')


def sanitize_payload(payload: dict) -> dict:
    """Return a copy of payload with sensitive fields removed or masked."""
    safe = {}
    for k, v in payload.items():
        kl = k.lower()
        if any(s in kl for s in ('pan', 'card_number', 'cvv', 'cvc', 'secret', 'key', 'password')):
            safe[k] = 'REDACTED'
        else:
            safe[k] = v
    return safe


def audit_event(event_name: str, payload: dict):
    record = {
        'event': event_name,
        'payload': sanitize_payload(payload)
    }
    logger.info(json.dumps(record))
