"""
User Vector Engine

Builds the combined user conditioning vector by processing baseline and recent check-ins,
then weights them using influence factors derived from performance classification.
"""

import numpy as np

from backend.database.db import create_conn
from backend.engines.base_vector_math import normalize, weighted_similarity
from backend.engines.scalars import (
    get_conditioning_scalar_from_classification,
    calculate_current_activity_scalar,
    classify_conditioning_level,
)

# Dimensions tracked for conditioning
DIMENSIONS = ["sleep_quality", "stress_level", "energy_level", "soreness_level"]


def get_baseline_vector(user_id: int) -> np.ndarray:
    """
    Retrieve the user's first check-in to use as a baseline conditioning vector.
    """

    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT {', '.join(DIMENSIONS)}
        FROM daily_checkins
        WHERE user_id = ?
        ORDER BY check_in_date ASC
        LIMIT 1
    """,
        (user_id,),
    )

    row = cursor.fetchone()
    if not row:
        raise ValueError("No baseline check-in found.")
    return np.array([row[dim] for dim in DIMENSIONS])


def get_recent_vector(user_id: int, days: int = 7) -> np.ndarray:
    """
    Calculate the average vector over recent check-ins.
    """
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT {', '.join(DIMENSIONS)}
        FROM daily_checkins
        WHERE user_id = ?
          AND check_in_date >= date('now', ?)
    """,
        (user_id, f"-{days} days"),
    )
    rows = cursor.fetchall()
    if not rows:
        raise ValueError("No recent check-ins found.")
    vectors = [np.array([row[dim] for dim in DIMENSIONS]) for row in rows]
    return np.mean(vectors, axis=0)


def combine_user_vector(
    user_id: int, initial_activity_level: str, days: int = 7
) -> dict:
    """
    Generate the user's combined conditioning vector using influence-scaled weighting.

    Returns:
        dict: {
            "raw_vector": List[float],
            "normalized_vector": List[float],
            "conditioning_level": str,
            "conditioning_scalar": float,
            "similarity_to_baseline": float
        }
    """
    baseline = get_baseline_vector(user_id)
    recent = get_recent_vector(user_id, days)

    # Compare recent to baseline to get similarity
    similarity = weighted_similarity(recent, baseline)
    classification = classify_conditioning_level(similarity)
    conditioning_scalar = get_conditioning_scalar_from_classification(classification)

    # Final influence scalar from activity and metrics
    activity_scalar = calculate_current_activity_scalar(user_id, initial_activity_level)

    # Use activity_scalar to override the blend weight
    blend_weight = 1.0 - activity_scalar
    blend_weight = max(0.0, min(blend_weight, 1.0))

    # Combine vectors
    combined = (1 - blend_weight) * baseline + blend_weight * recent
    combined_normalized = normalize(combined)

    return {
        "raw_vector": combined.tolist(),
        "normalized_vector": combined_normalized.tolist(),
        "conditioning_level": classification,
        "conditioning_scalar": conditioning_scalar,
        "similarity_to_baseline": round(similarity, 4),
    }
