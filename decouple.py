"""Lightweight shim for `python-decouple` used in tests.

This module provides a minimal `config` function that reads from
environment variables. It's intended only for local test runs where
installing `python-decouple` is not possible. In CI or production,
install the real `python-decouple` package instead and remove this shim.
"""
import os
from typing import Any, Callable


def _apply_cast(value: str, cast: Callable) -> Any:
    try:
        return cast(value)
    except Exception:
        return value


def config(key: str, default=None, cast: Callable = None):
    """Return an environment variable or default; optionally cast it.

    Args:
        key: environment variable name
        default: fallback value when env var not set
        cast: callable to convert the string value (e.g., int, bool)

    Returns:
        The environment value, optionally cast, or the default.
    """
    val = os.environ.get(key, None)
    if val is None:
        return default
    if cast:
        return _apply_cast(val, cast)
    return val
