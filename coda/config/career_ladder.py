"""
Career Ladder Configuration

Defines track boundaries and tier calculation rules for the career ladder system.

TRACKS:
- FOUNDATION: Entry level (0-349 points)
- GROWTH: Main progression track (350-799 points)
- PROFESSIONAL: Advanced track (800-1199 points)
- LEAD: Leadership track (1200+ points)

TIERS:
- Linear bucket distribution within each track
- Tier = 1 + floor((points - min_points) / bucket_size)
- Clamped between 1 and max_tiers for track
"""

TRACKS = {
    "FOUNDATION": {
        "tiers": 5,
        "min_points": 0,
        "max_points": 349,
    },
    "GROWTH": {
        "tiers": 18,
        "min_points": 350,
        "max_points": 799,
    },
    "PROFESSIONAL": {
        "tiers": 5,
        "min_points": 800,
        "max_points": 1199,
    },
    "LEAD": {
        "tiers": 3,
        "min_points": 1200,
        "max_points": None,  # No upper limit
    },
}


def get_track_for_points(total_points: float) -> str:
    """
    Determine which track a point total falls into.

    Args:
        total_points: Total lifetime points

    Returns:
        Track name (FOUNDATION, GROWTH, PROFESSIONAL, or LEAD)
    """
    if total_points < TRACKS["GROWTH"]["min_points"]:
        return "FOUNDATION"
    elif total_points < TRACKS["PROFESSIONAL"]["min_points"]:
        return "GROWTH"
    elif total_points < TRACKS["LEAD"]["min_points"]:
        return "PROFESSIONAL"
    else:
        return "LEAD"


def calculate_tier_for_track(track: str, total_points: float) -> int:
    """
    Calculate tier number within a track based on points.

    Args:
        track: Track name (FOUNDATION, GROWTH, PROFESSIONAL, LEAD)
        total_points: Total lifetime points

    Returns:
        Tier number (1 to max_tiers for track)
    """
    if track not in TRACKS:
        return 1

    track_config = TRACKS[track]
    min_points = track_config["min_points"]
    max_points = track_config["max_points"]
    max_tiers = track_config["tiers"]

    # Clamp points to track range
    if max_points is not None:
        points_in_track = min(max(total_points, min_points), max_points)
    else:
        points_in_track = max(total_points, min_points)

    # Calculate bucket size
    points_range = (
        (max_points - min_points) if max_points else (points_in_track - min_points + 1)
    )
    bucket_size = points_range / max_tiers

    # Calculate tier (1-indexed)
    tier = 1 + int((points_in_track - min_points) / bucket_size)

    # Clamp to valid range
    tier = max(1, min(tier, max_tiers))

    return tier


def get_track_boundaries():
    """
    Get all track boundaries for reporting/analysis.

    Returns:
        List of (track_name, min_points, max_points, tiers)
    """
    return [
        (track, config["min_points"], config["max_points"], config["tiers"])
        for track, config in TRACKS.items()
    ]
