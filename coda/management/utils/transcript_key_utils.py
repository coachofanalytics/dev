"""
Utility functions for extracting and matching transcript keys from URLs.

Transcript keys are used as the canonical join key between TaskLinks and Meeting
for transcripts.gotomeeting.com URLs.
"""

import re
from typing import Optional


def extract_transcript_key(url: str) -> Optional[str]:
    """
    Extract transcript key from transcripts.gotomeeting.com URL.

    Expected format: https://transcripts.gotomeeting.com/#/s/<key>

    Args:
        url: URL string (may be None or empty)

    Returns:
        Transcript key string if found (hex characters only, 8-128 chars), None otherwise

    Notes:
        - Only captures hex characters [0-9a-fA-F]
        - Stops at first non-hex character (handles malformed keys like "...https")
        - Requires key length >= 8 and <= 128
    """
    if not url or not isinstance(url, str):
        return None

    # Pattern: #/s/<key> where key is hex characters only [0-9a-fA-F]
    # The key appears after '#/s/' in the URL
    # Capture only hex characters and stop at first non-hex
    pattern = r"#/s/([0-9a-fA-F]+)"
    match = re.search(pattern, url)

    if match:
        key = match.group(1)
        # Validate key length: >= 8 and <= 128
        if 8 <= len(key) <= 128:
            return key
        # Key too short or too long - return None
        return None

    return None


def is_transcript_url(url: str) -> bool:
    """
    Check if URL is a transcripts.gotomeeting.com URL.

    Args:
        url: URL string

    Returns:
        True if URL is a transcript URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    return "transcripts.gotomeeting.com" in url.lower()
