from typing import Any, Dict, Optional
from datetime import datetime
import json
from fastapi.encoders import jsonable_encoder


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format string."""
    return dt.isoformat()


def to_dict(obj: Any) -> Dict:
    """Convert any object to dictionary."""
    return json.loads(json.dumps(jsonable_encoder(obj)))


def safe_get(data: Dict, *keys: str, default: Any = None) -> Optional[Any]:
    """Safely get nested dictionary values."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is None:
            return default
    return current


def remove_none_values(data: Dict) -> Dict:
    """Remove None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}
