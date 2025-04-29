"""
Scalar Module.

Handles mapping of conditioning classifications and activity levels
into numerical scalars for vector operations, performance evaluation,
and dynamic target setting.
"""

import numpy as np
from backend.database.db import create_conn


def get_conditioning_scalar_from_classification(conditioning_level: str) -> float:
    """
    Get scalar value based on conditioning classification.

    Parameters:
        conditioning_level (str): 'Elite', 'Advanced', etc.

    Returns:
        float: Scalar value between 0.0 and 1.0
    """
    scalar_map = {
        "Elite": 0.9,
        "Advanced": 0.85,
        "Intermediate": 0.65,
        "Novice": 0.4,
        "Beginner": 0.2,
    }
    return scalar_map.get(conditioning_level, 0.5)


def classify_conditioning_level(similarity_score: float) -> str:
    """
    Categorize a similarity score into a conditioning classification label.
    """
    if similarity_score >= 0.9:
        return "Elite"
    elif similarity_score >= 0.75:
        return "Advanced"
    elif similarity_score >= 0.6:
        return "Intermediate"
    elif similarity_score >= 0.4:
        return "Novice"
    else:
        return "Beginner"


def classify_activity_level(activity_level: str) -> float:
    """
    Classify activity level string into a numeric scalar.

    Parameters:
        activity_level (str): 'Sedentary', 'Casual', etc.

    Returns:
        float: Scalar value.
    """
    activity_scalar_map = {
        "Sedentary": 0.2,
        "Casual": 0.5,
        "Moderate": 0.75,
        "Active": 1.0,
        "Intense": 1.5,
    }
    return activity_scalar_map.get(activity_level, 0.5)  # Default neutral if unknown


def get_user_checkin_count(user_id: int) -> int:
    """
    Get total number of check-ins a user has made.

    Parameters:
        user_id (int): The user's ID.

    Returns:
        int: Number of check-ins.
    """
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM daily_checkins
        WHERE user_id = ?
    """,
        (user_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else 0


def calculate_avg_sleep_quality(user_id: int, days: int = 7) -> float:
    """
    Calculate the user's average sleep quality over recent check-ins.

    Parameters:
        user_id (int): The user's ID.
        days (int): Lookback window.

    Returns:
        float: Average sleep quality (0–10 scale).
    """
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sleep_quality
        FROM daily_checkins
        WHERE user_id = ?
          AND sleep_quality IS NOT NULL
          AND check_in_date >= date('now', ?)
    """,
        (user_id, f"-{days} days"),
    )

    rows = cursor.fetchall()
    sleep_scores = [
        row["sleep_quality"] for row in rows if row["sleep_quality"] is not None
    ]

    if not sleep_scores:
        return 0.0  # No data fallback

    avg_sleep = np.mean(sleep_scores)
    return round(avg_sleep, 2)


def calculate_current_activity_scalar(
    user_id: int, initial_activity_level: str
) -> float:
    """
    Calculate final current activity scalar based on engagement and recovery metrics.

    Parameters:
        user_id (int): The user's ID.
        initial_activity_level (str): Initial activity level at registration.

    Returns:
        float: Activity scalar value.
    """
    # 1. Base scalar from initial activity level
    base_scalar = classify_activity_level(initial_activity_level)

    # 2. Check-in based engagement score (0.0 to 1.0)
    checkin_count = get_user_checkin_count(user_id)
    checkin_scalar = min(checkin_count / 30.0, 1.0)

    # 3. Sleep quality scalar (0.0 to 1.0)
    avg_sleep_quality = calculate_avg_sleep_quality(user_id)
    sleep_scalar = min(avg_sleep_quality / 10.0, 1.0)

    # 4. Nutrition quality scalar (placeholder, assume perfect)
    nutrition_scalar = 1.0

    # 5. Final scalar blend
    final_scalar = base_scalar * (
        0.5 * checkin_scalar + 0.25 * sleep_scalar + 0.25 * nutrition_scalar
    )

    return round(final_scalar, 3)
