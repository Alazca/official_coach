import numpy as np
from typing import Dict, Optional, Union

from backend.database.db import create_conn
from backend.engines.metrics import get_strength_metrics, get_conditioning_metrics
from backend.models.models import ActivityLevel


ACTIVITY_SCALAR_MAP = {
    ActivityLevel.SEDENTARY: 0.2,
    ActivityLevel.CASUAL: 0.5,
    ActivityLevel.MODERATE: 0.75,
    ActivityLevel.ACTIVE: 0.9,
    ActivityLevel.INTENSE: 1.0,
}


def compute_influence_scalars(
    user_id: int, days: int = 7, weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Compute influence factors (scalars) for user_vector and target_vector:
      - Fetch raw metrics
      - Normalize each to [0.0,1.0]
      - Apply weights and return combined scalar

    Returns dict of each normalized scalar plus final 'influence_scalar'.
    """
    strength = get_strength_metrics(user_id, days)
    cond = get_conditioning_metrics(user_id, days)

    # Default weights
    if weights is None:
        weights = {
            "combined_strength": 0.3,
            "total_volume": 0.2,
            "volume_percentile": 0.1,
            "weekly_volume": 0.15,
            "training_days": 0.1,
            "volume_change_pct": 0.05,
            "intensity_avg": 0.05,
            "consistency_pct": 0.03,
        }

    # Normalize metrics
    norm_strength = min(
        strength["combined_strength"] / 2.0, 1.0
    )  # assume 2x bodyweight as cap
    norm_total_vol = min(strength["total_volume"] / 10000.0, 1.0)  # cap at 10k
    norm_vol_pct = strength["volume_percentile"] / 100.0

    norm_weekly = min(cond["weekly_volume"] / 20000.0, 1.0)
    norm_days = cond["training_days"] / days
    norm_change = max(min((cond["volume_change_pct"] + 100) / 200.0, 1.0), 0.0)
    norm_intensity = min(cond["intensity_avg"] / 100.0, 1.0)
    norm_consistency = max(1.0 - cond["consistency_pct"] / 100.0, 0.0)

    scalars = {
        "combined_strength": norm_strength,
        "total_volume": norm_total_vol,
        "volume_percentile": norm_vol_pct,
        "weekly_volume": norm_weekly,
        "training_days": norm_days,
        "volume_change_pct": norm_change,
        "intensity_avg": norm_intensity,
        "consistency_pct": norm_consistency,
    }

    # Weighted sum
    influence_scalar = sum(scalars[k] * weights.get(k, 0) for k in scalars)
    scalars["influence_scalar"] = round(influence_scalar, 3)

    return scalars


def classify_activity_level(activity_level: str) -> float:
    """
    Classify activity level string into a numeric scalar.

    Parameters:
        activity_level (str): 'Sedentary', 'Casual', etc.

    Returns:
        float: Scalar value.
    """
    if isinstance(activity_level, str):
        try:
            activity_level = ActivityLevel(activity_level.capitalize())
        except ValueError:
            # Unknown string → neutral
            return 0.5

    return ACTIVITY_SCALAR_MAP.get(activity_level, 0.5)


def calculate_overall_fitness_scalar(
    strength_conditioning_scalar: float,
    activity_level_scalar: float,
    strength_weight: float = 0,
    activity_weight: float = 0,
) -> float:
    """
    Calculates an overall fitness scalar based on weighted strength/conditioning and activity level.

    Returns a float between 0.0 and 1.0.
    """
    if not (0.0 <= strength_conditioning_scalar <= 1.0):
        raise ValueError("Strength and conditioning scalar must be between 0.0 and 1.0")
    if not (0.0 <= activity_level_scalar <= 1.0):
        raise ValueError("Activity level scalar must be between 0.0 and 1.0")
    if (
        strength_weight < 0
        or activity_weight < 0
        or abs(strength_weight + activity_weight - 1.0) > 1e-6
    ):
        raise ValueError("Weights must be non-negative and sum to 1.0")

    return round(
        strength_conditioning_scalar * strength_weight
        + activity_level_scalar * activity_weight,
        3,
    )


def compute_final_scalar(
    user_id: int,
    days: int = 7,
    strength_weight: float = 0.6,
    activity_weight: float = 0.4,
) -> float:
    """
    Computes and persists the final scalar combining overall influence and activity level.

    Steps:
      1. Calculate the influence scalar (0.0–1.0).
      2. Fetch and map currentActivityLevel to a scalar (0.0–1.0).
      3. Compute final_scalar = strength_weight * influence + activity_weight * activity_scalar.
      4. Persist new activity level derived from final_scalar.

    Returns a float between 0.0 and 1.0.
    """
    # 1) Influence scalar
    scalars = compute_influence_scalars(user_id, days)
    influence = scalars["influence_scalar"]

    # 2) Activity level scalar mapping
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT currentActivityLevel FROM users WHERE user_id = ?", (user_id,)
        )
        row = cur.fetchone()
    level = row[0] if row else None
    level_str = level if isinstance(level, str) else ""

    activity_map: Dict[str, float] = {
        "Sedentary": 0.2,
        "Casual": 0.5,
        "Moderate": 0.75,
        "Active": 0.90,
        "Intense": 1.0,
    }
    activity_scalar = activity_map.get(level_str, 0.5)

    # 3) Final weighted blend
    final_scalar = calculate_overall_fitness_scalar(
        strength_conditioning_scalar=influence,
        activity_level_scalar=activity_scalar,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )

    # 4) Persist updated activity level
    # Map final_scalar to discrete level
    if final_scalar >= 1.0:
        new_level = "Intense"
    elif final_scalar >= 0.9:
        new_level = "Active"
    elif final_scalar >= 0.75:
        new_level = "Moderate"
    elif final_scalar >= 0.5:
        new_level = "Casual"
    else:
        new_level = "Sedentary"

    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET currentActivityLevel = ? WHERE user_id = ?",
            (new_level, user_id),
        )
        conn.commit()

    return final_scalar


def classify_overall_fitness_tier(final_scalar: float) -> str:
    """
    Categorize the final fitness scalar into tiers:
      - 'Elite'       : final_scalar >= 1.0
      - 'Advanced'    : final_scalar >= 0.9
      - 'Intermediate': final_scalar >= 0.5
      - 'Novice'      : final_scalar >= 0.2
      - 'Beginner'    : final_scalar < 0.2
    """
    if final_scalar >= 1.0:
        return "Elite"
    elif final_scalar >= 0.9:
        return "Advanced"
    elif final_scalar >= 0.5:
        return "Intermediate"
    elif final_scalar >= 0.2:
        return "Novice"
    else:
        return "Beginner"
