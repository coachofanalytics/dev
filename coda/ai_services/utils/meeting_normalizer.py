"""
Meeting Normalization Utilities

Provides utilities for normalizing meeting topics, URLs, extracting requirement codes,
and extracting candidate activity tags.
Used for analysis and improving matching between meetings and tasks.

Phase 2A+1: Meeting analysis and normalization layer.
"""

import re
from typing import List, Optional


def normalize_topic(topic: str) -> str:
    """
    Normalize meeting topic for consistent grouping and matching.

    Rules:
    - Lowercase
    - Trim whitespace
    - Collapse multiple whitespace to single space
    - Remove obvious noise tokens (recording, session, meeting, gotomeeting)
    - Strip repeated punctuation
    - Conservative: does not destroy meaning

    Args:
        topic: Raw meeting topic string

    Returns:
        Normalized topic string
    """
    if not topic:
        return ""

    # Lowercase and trim
    normalized = topic.lower().strip()

    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove noise tokens (only if they appear as standalone words)
    # Use negative lookbehind/lookahead for word boundaries (handles underscores correctly)
    noise_tokens = ["recording", "session", "meeting", "gotomeeting", "g2m"]
    for token in noise_tokens:
        # Remove token if it's a standalone word (word boundaries using lookbehind/lookahead)
        pattern = r"(?<!\w)" + re.escape(token) + r"(?!\w)"
        normalized = re.sub(pattern, "", normalized)

    # Collapse whitespace again (in case noise removal left gaps)
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip repeated punctuation (keep single punctuation, remove duplicates)
    normalized = re.sub(r"([!?.]){2,}", r"\1", normalized)
    normalized = re.sub(r"[-]{2,}", "-", normalized)
    normalized = re.sub(r"[_]{2,}", "_", normalized)

    # Trim again
    normalized = normalized.strip()

    # Remove leading/trailing punctuation
    normalized = re.sub(r"^[^\w]+|[^\w]+$", "", normalized)

    return normalized


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize URL by stripping querystring, fragments, and trailing slashes.

    Useful for matching and deduplication.

    Args:
        url: Raw URL string

    Returns:
        Normalized URL string, or None if input is empty/invalid
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()
    if not url:
        return None

    # Remove fragment (everything after #)
    if "#" in url:
        url = url.split("#")[0]

    # Remove querystring (everything after ?)
    if "?" in url:
        url = url.split("?")[0]

    # Remove trailing slash
    url = url.rstrip("/")

    return url if url else None


def normalize_gotomeeting_transcript_url(
    share_url: Optional[str] = None,
    download_url: Optional[str] = None,
    share_id: Optional[str] = None,
    token: Optional[str] = None,
) -> Optional[str]:
    """
    Normalize GoToMeeting transcript/recording URL to canonical format.

    Canonical format: https://transcripts.gotomeeting.com/#/s/<token>

    Strategy:
    1. Parse URLs using urlparse to properly handle fragments
    2. Extract token from fragment first (fragment contains "/s/<token>")
    3. Fall back to query params (shareId/token), then path
    4. Use provided token/share_id if available
    5. Never return bare host without token

    Args:
        share_url: Share URL from API (e.g., from recording.shareUrl)
        download_url: Download URL from API (e.g., from recording.downloadUrl)
        share_id: Share ID if provided separately
        token: Token if provided directly

    Returns:
        Canonical transcript URL (https://transcripts.gotomeeting.com/#/s/<token>),
        or None if no valid token can be extracted
    """
    import logging
    from urllib.parse import parse_qs, urlparse

    logger = logging.getLogger(__name__)
    CANONICAL_BASE = "https://transcripts.gotomeeting.com/#/s/"
    CANONICAL_HOST = "transcripts.gotomeeting.com"

    # DEBUG: Show fragment parsing for canonical URL
    if share_url and "transcripts.gotomeeting.com" in share_url:
        parsed = urlparse(share_url)
        logger.debug(
            f"🔍 URL Parse Debug: share_url={share_url}, "
            f"scheme={parsed.scheme}, netloc={parsed.netloc}, "
            f"path={parsed.path}, fragment={parsed.fragment}, "
            f"query={parsed.query}"
        )

    # Extract token from various sources
    extracted_token = None

    # Priority 1: Check if share_url is already a canonical transcripts URL
    if share_url:
        share_url = share_url.strip()
        parsed = urlparse(share_url)

        # Check if host is transcripts.gotomeeting.com
        if parsed.netloc == CANONICAL_HOST or parsed.netloc.endswith(
            f".{CANONICAL_HOST}"
        ):
            # Check fragment first (fragment contains "/s/<token>")
            if parsed.fragment:
                # Fragment format: "/s/<token>" or "s/<token>" (may have query string after)
                # Extract token from fragment, handling query strings
                fragment_clean = parsed.fragment.split("?")[
                    0
                ]  # Remove query from fragment
                fragment_match = re.search(r"/?s/([^/?&#]+)", fragment_clean)
                if fragment_match:
                    extracted_token = fragment_match.group(1).strip()
                    # Additional cleanup: remove any remaining query/fragment chars
                    extracted_token = (
                        extracted_token.split("?")[0]
                        .split("#")[0]
                        .split("&")[0]
                        .strip()
                    )
                    logger.debug(f"✅ Extracted token from fragment: {extracted_token}")
                elif fragment_clean.startswith("/s/") or fragment_clean.startswith(
                    "s/"
                ):
                    # Direct fragment token
                    token_part = (
                        fragment_clean.lstrip("/s/").split("/")[0].split("?")[0]
                    )
                    if token_part:
                        extracted_token = token_part
                        logger.debug(
                            f"✅ Extracted token from fragment (direct): {extracted_token}"
                        )

            # If we have token from fragment, always construct clean canonical URL (don't return original with query strings)
            if extracted_token:
                return f"{CANONICAL_BASE}{extracted_token}"

            # If already canonical format (and no token extracted from fragment), return as-is
            if share_url.startswith(CANONICAL_BASE):
                return share_url

            # Try query params as fallback
            if parsed.query:
                query_params = parse_qs(parsed.query)
                extracted_token = (
                    query_params.get("token", [None])[0]
                    or query_params.get("shareId", [None])[0]
                    or query_params.get("share_id", [None])[0]
                )
                if extracted_token:
                    logger.debug(f"✅ Extracted token from query: {extracted_token}")

            # Try path as fallback
            if not extracted_token and parsed.path:
                path_match = re.search(r"/s/([^/?&#]+)", parsed.path)
                if path_match:
                    extracted_token = path_match.group(1)
                    logger.debug(f"✅ Extracted token from path: {extracted_token}")

        # For non-transcripts URLs, try to extract token from various patterns
        elif not extracted_token:
            # Check query parameters
            if "shareId=" in share_url or "token=" in share_url:
                match = re.search(r"(?:shareId|token)=([^&]+)", share_url)
                if match:
                    extracted_token = match.group(1)
                    logger.debug(
                        f"✅ Extracted token from query string: {extracted_token}"
                    )

            # Check path for /s/ pattern
            if not extracted_token and "/s/" in share_url:
                match = re.search(r"/s/([^/?&#]+)", share_url)
                if match:
                    extracted_token = match.group(1)
                    logger.debug(f"✅ Extracted token from path: {extracted_token}")

    # Priority 2: Use provided token or share_id
    if not extracted_token:
        extracted_token = token or share_id
        if extracted_token:
            logger.debug(f"✅ Using provided token/share_id: {extracted_token}")

    # Priority 3: Try to extract from download_url
    if not extracted_token and download_url:
        download_url = download_url.strip()
        parsed = urlparse(download_url)

        # Check query params
        if parsed.query:
            query_params = parse_qs(parsed.query)
            extracted_token = (
                query_params.get("token", [None])[0]
                or query_params.get("shareId", [None])[0]
                or query_params.get("share_id", [None])[0]
            )
            if extracted_token:
                logger.debug(
                    f"✅ Extracted token from download_url query: {extracted_token}"
                )

        # Check path
        if not extracted_token and parsed.path:
            path_match = re.search(r"/s/([^/?&#]+)", parsed.path)
            if path_match:
                extracted_token = path_match.group(1)
                logger.debug(
                    f"✅ Extracted token from download_url path: {extracted_token}"
                )

    # Construct canonical URL if we have a token
    if extracted_token:
        # Clean token (remove any URL encoding, whitespace, query fragments)
        extracted_token = (
            extracted_token.strip().split("?")[0].split("#")[0].split("&")[0]
        )
        if extracted_token:
            canonical_url = f"{CANONICAL_BASE}{extracted_token}"
            logger.debug(f"✅ Constructed canonical URL: {canonical_url}")
            return canonical_url

    # GUARD: Never return bare host
    # If no token found, return None (don't store generic provider links)
    logger.debug(f"⚠️  No token extracted, returning None (not storing bare host)")
    return None


def extract_requirement_code(text: str, allow_multiple: bool = False) -> Optional[str]:
    """
    Extract requirement code from text (e.g., "REQ-5755").

    Looks for pattern: REQ-#### (3-6 digits, case-insensitive).
    Tolerates spaces/dashes: "REQ - 1234", "REQ-1234", "req 1234"
    Returns normalized uppercase string like "REQ-5755" or None if not found.

    IMPORTANT: Only matches "REQ-####" pattern, NOT "Requirement-####" or similar.
    This ensures we don't accidentally treat meeting titles like "Requirement-508" as requirement codes.

    If multiple codes found:
    - If allow_multiple=False (default): returns first match and logs warning
    - If allow_multiple=True: returns first match (for now; future: could return list)

    Args:
        text: Raw text string (meeting topic, task description, etc.)
        allow_multiple: If True, allows multiple codes (future enhancement)

    Returns:
        Normalized requirement code string (e.g., "REQ-5755") or None
    """
    import logging

    logger = logging.getLogger(__name__)

    if not text or not isinstance(text, str):
        return None

    # Pattern variations (ONLY matches "REQ-####", NOT "Requirement-####"):
    # 1. REQ-#### (standard)
    # 2. REQ - #### (with spaces around dash)
    # 3. REQ #### (without dash, with space)
    # All case-insensitive, word boundaries
    # Explicitly excludes "Requirement-####" patterns to avoid false positives
    patterns = [
        r"\bREQ\s*-\s*(\d{3,6})\b",  # REQ-1234 or REQ - 1234 (NOT Requirement-1234)
        r"\bREQ\s+(\d{3,6})\b",  # REQ 1234 (space, no dash)
    ]

    matches = []
    for pattern in patterns:
        found = re.finditer(pattern, text, re.IGNORECASE)
        for match in found:
            req_number = match.group(1)
            matches.append(f"REQ-{req_number}")

    if not matches:
        return None

    # Normalize to uppercase
    normalized_matches = [m.upper() for m in matches]

    # If multiple codes found, log warning and return first
    if len(normalized_matches) > 1:
        logger.warning(
            f"Multiple REQ codes found in text: {normalized_matches}. "
            f"Using first: {normalized_matches[0]}"
        )
        if not allow_multiple:
            # For now, return first match
            return normalized_matches[0]

    return normalized_matches[0]


def extract_candidate_activity_tags(topic: str) -> List[str]:
    """
    Extract candidate activity tags from meeting topic using keyword matching.

    This is NOT a final mapping engine; it's a heuristic to help analyze naming patterns.
    Rule-based and simple (keyword contains checks).

    Args:
        topic: Meeting topic string (can be raw or normalized)

    Returns:
        List of candidate activity tag strings (e.g., ["pbr", "client_training"])
    """
    if not topic:
        return []

    topic_lower = topic.lower()
    tags = []

    # PBR / Backlog Refinement
    if any(
        keyword in topic_lower
        for keyword in [
            "pbr",
            "backlog refinement",
            "product backlog",
            "backlog review",
        ]
    ):
        tags.append("pbr")

    # Training sessions
    if any(
        keyword in topic_lower
        for keyword in ["client training", "customer training", "client session"]
    ):
        tags.append("client_training")

    if any(
        keyword in topic_lower
        for keyword in ["internal training", "staff training", "team training"]
    ):
        tags.append("internal_training")

    if any(
        keyword in topic_lower
        for keyword in ["self training", "self-training", "one on one", "1-on-1", "1:1"]
    ):
        tags.append("self_training")

    # Daily updates / standups
    if any(
        keyword in topic_lower
        for keyword in ["daily update", "daily standup", "standup", "daily sync"]
    ):
        tags.append("daily_update")

    # Sprint / Agile
    if any(
        keyword in topic_lower
        for keyword in [
            "sprint",
            "sprint planning",
            "sprint review",
            "sprint retrospective",
        ]
    ):
        tags.append("sprint")

    # Demo / Presentation
    if any(
        keyword in topic_lower
        for keyword in ["demo", "demonstration", "presentation", "showcase"]
    ):
        tags.append("demo")

    # Review / Retrospective
    if any(
        keyword in topic_lower
        for keyword in ["review", "retrospective", "retro", "assessment"]
    ):
        tags.append("review")

    # Planning
    if any(keyword in topic_lower for keyword in ["planning", "plan", "roadmap"]):
        tags.append("planning")

    # Support / Job support
    if any(
        keyword in topic_lower
        for keyword in ["job support", "client support", "support session", "help"]
    ):
        tags.append("job_support")

    return tags
