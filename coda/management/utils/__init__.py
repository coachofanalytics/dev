"""
Management utilities package.

This package contains utility modules. To maintain backward compatibility
with imports from management.utils (the parent module), we re-export
functions from the parent utils.py module.

NOTE: When both management/utils.py (module) and management/utils/ (package) exist,
Python will import the package. This __init__.py re-exports from the parent module
to maintain backward compatibility.
"""

import importlib.util
import os
# Re-export functions from parent utils.py module to maintain backward compatibility
# Load the parent utils.py module using importlib to avoid circular import
import sys

# Get the path to the parent utils.py module (management/utils.py)
_current_file = os.path.abspath(__file__)
_package_dir = os.path.dirname(_current_file)  # management/utils/
_parent_dir = os.path.dirname(_package_dir)  # management/
_parent_utils_path = os.path.join(_parent_dir, "utils.py")

# Load the parent utils.py module explicitly
_parent_utils = None
if os.path.exists(_parent_utils_path):
    try:
        spec = importlib.util.spec_from_file_location(
            "management.utils_module", _parent_utils_path
        )
        if spec and spec.loader:
            _parent_utils = importlib.util.module_from_spec(spec)
            # Add to sys.modules with a different name to avoid conflicts
            sys.modules["management.utils_module"] = _parent_utils
            spec.loader.exec_module(_parent_utils)
    except Exception as e:
        # Log error but continue - will use fallbacks
        import logging

        logging.getLogger(__name__).warning(f"Could not load parent utils.py: {e}")
        _parent_utils = None

# Export transcript_key_utils functions
from .transcript_key_utils import extract_transcript_key, is_transcript_url


# Define fallback implementations first (so they're always available)
def _fallback_unique_slug_generator(instance, new_slug=None):
    import random
    import string

    from django.utils.text import slugify

    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(getattr(instance, "title", str(instance)))

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if qs_exists:
        randstr = "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(4)
        )
        new_slug = f"{slug}-{randstr}"
        return _fallback_unique_slug_generator(instance, new_slug=new_slug)
    return slug


def _fallback_split_num_str(my_str):
    num = [x for x in my_str if x.isdigit()]
    num = "".join(num)
    if not num:
        num = None
    return num


# Explicitly export commonly used functions from parent utils.py for better IDE support and direct access
# Always define these at module level so imports work
if _parent_utils and hasattr(_parent_utils, "unique_slug_generator"):
    unique_slug_generator = _parent_utils.unique_slug_generator
else:
    unique_slug_generator = _fallback_unique_slug_generator

if _parent_utils and hasattr(_parent_utils, "split_num_str"):
    split_num_str = _parent_utils.split_num_str
else:
    split_num_str = _fallback_split_num_str


# Define fallback for is_valid_evidence_url
def _fallback_is_valid_evidence_url(url: str) -> bool:
    """Fallback implementation of is_valid_evidence_url."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    placeholder_patterns = [
        "https://...",
        "http://...",
        "https://www.",
        "http://www.",
    ]
    if any(url.lower().startswith(pattern.lower()) for pattern in placeholder_patterns):
        return False
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return bool(parsed.netloc)
    except Exception:
        return False


# Explicitly export commonly used functions from parent utils.py for better IDE support and direct access
# Always define these at module level so imports work
if _parent_utils and hasattr(_parent_utils, "is_valid_evidence_url"):
    is_valid_evidence_url = _parent_utils.is_valid_evidence_url
else:
    is_valid_evidence_url = _fallback_is_valid_evidence_url

# Export other functions if available (use __getattr__ for the rest)
if _parent_utils:
    if hasattr(_parent_utils, "paytime"):
        paytime = _parent_utils.paytime
    if hasattr(_parent_utils, "payinitial"):
        payinitial = _parent_utils.payinitial
    if hasattr(_parent_utils, "paymentconfigurations"):
        paymentconfigurations = _parent_utils.paymentconfigurations
    if hasattr(_parent_utils, "deductions"):
        deductions = _parent_utils.deductions
    if hasattr(_parent_utils, "loan_computation"):
        loan_computation = _parent_utils.loan_computation
    if hasattr(_parent_utils, "updateloantable"):
        updateloantable = _parent_utils.updateloantable
    if hasattr(_parent_utils, "get_tasks"):
        get_tasks = _parent_utils.get_tasks
    if hasattr(_parent_utils, "task_assignment_random"):
        task_assignment_random = _parent_utils.task_assignment_random


# Use __getattr__ to dynamically proxy any other attributes from parent utils.py module
# This allows any import from management.utils to work transparently
def __getattr__(name):
    """Dynamically proxy attributes from parent utils.py module."""
    if _parent_utils and hasattr(_parent_utils, name):
        return getattr(_parent_utils, name)

    # If not found in parent, check if it's a transcript_key_utils function
    if name == "extract_transcript_key":
        return extract_transcript_key
    elif name == "is_transcript_url":
        return is_transcript_url

    # If still not found, raise AttributeError
    raise AttributeError(f"module 'management.utils' has no attribute '{name}'")


__all__ = [
    "unique_slug_generator",
    "split_num_str",
    "extract_transcript_key",
    "is_transcript_url",
    "paytime",
    "payinitial",
    "paymentconfigurations",
    "deductions",
    "loan_computation",
    "updateloantable",
    "get_tasks",
    "is_valid_evidence_url",
    "task_assignment_random",
]
