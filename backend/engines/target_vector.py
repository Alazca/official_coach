"""
Target Vector Engine

Generates a time-aware and readiness-scaled target vector representing
the user's intended conditioning profile based on goal, time, and activity level.
"""

import numpy as np

from datetime import datetime
from backend.engines.base_vector_math import interpolate_vectors, normalize
from backend.engines.scalars import (
    classify_activity_level,
    calculate_current_activity_scalar,
)


def get_timeline_ratio(start_date: str, end_date: str) -> float:
    """
    Calculate the ratio of progress through the goal timeline (0.0 to 1.0)
    using today's date as the current time marker.

    Parameters:
        start_date (str): Timeline start in 'YYYY-MM-DD'
        end_date (str): Timeline end in 'YYYY-MM-DD'

    Returns:
        float: Progress ratio from 0.0 (just started) to 1.0 (completed or past due)
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    today = datetime.today()

    total_days = (end - start).days
    elapsed_days = (today - start).days

    if total_days <= 0:
        return 1.0
    return max(0.0, min(elapsed_days / total_days, 1.0))


def generate_target_vector(
    user_id: int,
    goal_vector: np.ndarray,
    baseline_vector: np.ndarray,
    start_date: str,
    end_date: str,
    current_activity_level: str,
    initial_activity_level: str,
) -> dict:
    """
    Generate a target conditioning vector based on the user's goal and timeline.

    Parameters:
        goal_vector (np.ndarray): Ideal conditioning vector for the goal
        baseline_vector (np.ndarray): Starting vector
        start_date (str): Goal timeline start (YYYY-MM-DD)
        end_date (str): Goal timeline end (YYYY-MM-DD)
        current_activity_level (str): User's current level
        initial_activity_level (str): User's initial level

    Returns:
        dict: {
            "target_vector": List[float],
            "normalized_vector": List[float],
            "activity_scalar": float,
            "timeline_ratio": float
        }
    """
    timeline_ratio = get_timeline_ratio(start_date, end_date)
    activity_scalar = classify_activity_level(current_activity_level)

    # Interpolate between baseline and goal using timeline progress
    interpolated = interpolate_vectors(baseline_vector, goal_vector, timeline_ratio)

    # Calculate scalar from user's activity & metrics
    activity_scalar = calculate_current_activity_scalar(
        user_id=user_id,  # Optional override if needed
        initial_activity_level=initial_activity_level,
    )

    # Scale the target up based on current activity readiness
    scaled = interpolated * activity_scalar
    normalized = normalize(scaled)

    return {
        "target_vector": scaled.tolist(),
        "normalized_vector": normalized.tolist(),
        "activity_scalar": round(activity_scalar, 3),
        "timeline_ratio": round(timeline_ratio, 3),
    }
