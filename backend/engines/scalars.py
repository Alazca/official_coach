import numpy as np
import logging

from typing import Dict, Optional, Union

from backend.database.db import create_conn
from backend.engines.metrics import get_strength_metrics, get_conditioning_metrics
from backend.models.models import ActivityLevel


# Configure logger
logger = logging.getLogger(__name__)

# Mapping of activity levels to scalar values
ACTIVITY_SCALAR_MAP = {
    ActivityLevel.SEDENTARY: 0.2,  # Very little activity
    ActivityLevel.CASUAL: 0.5,  # Light activity 1-2 days/week
    ActivityLevel.MODERATE: 0.75,  # Moderate activity 2-3 days/week
    ActivityLevel.ACTIVE: 0.9,  # Intense activity 3-5 days/week
    ActivityLevel.INTENSE: 1.0,  # Very intense activity 5-7 days/week
}


def compute_influence_scalars(
    user_id: int, days: int = 7, weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Compute normalized influence factors for user vector calculations.

    Args:
        user_id: User identifier
        days: Lookback period in days
        weights: Optional custom weights for each metric

    Returns:
        Dictionary of normalized scalars (0-1) and final influence scalar
    """
    # Get raw metrics
    strength = get_strength_metrics(user_id, days)
    cond = get_conditioning_metrics(user_id, days)

    # Default weights if not provided
    if weights is None:
        weights = {
            "combined_strength": 0.3,  # 30% - Relative strength importance
            "total_volume": 0.2,  # 20% - Total work volume
            "volume_percentile": 0.1,  # 10% - Ranking among peers
            "weekly_volume": 0.15,  # 15% - Recent work capacity
            "training_days": 0.1,  # 10% - Training frequency
            "volume_change_pct": 0.05,  #  5% - Progress rate
            "intensity_avg": 0.05,  #  5% - Training intensity
            "consistency_pct": 0.05,  #  5% - Training consistency
        }

    # Validate weights sum to 1.0
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.01:  # Allow small floating point error
        logger.warning(f"Weights do not sum to 1.0 (sum: {weight_sum}), normalizing")
        weights = {k: v / weight_sum for k, v in weights.items()}

    # Normalize metrics to 0-1 scale
    # Strength metrics
    norm_strength = min(
        strength["combined_strength"] / 2.0, 1.0
    )  # Cap at 2x bodyweight
    norm_total_vol = min(strength["total_volume"] / 10000.0, 1.0)  # Cap at 10k volume
    norm_vol_pct = strength["volume_percentile"] / 100.0  # Already 0-100

    # Conditioning metrics
    norm_weekly = min(cond["weekly_volume"] / 20000.0, 1.0)  # Cap at 20k weekly volume
    norm_days = cond["training_days"] / min(days, 7)  # Cap at 7 days per week

    # Volume change: map -100% to +100% range to 0-1 scale
    norm_change = max(min((cond["volume_change_pct"] + 100) / 200.0, 1.0), 0.0)

    # Intensity: normalize based on a reasonable range
    norm_intensity = min(
        cond["intensity_avg"] / 100.0, 1.0
    )  # Cap at 100 weight per rep

    # Consistency: invert so higher is better (less variance)
    norm_consistency = max(1.0 - cond["consistency_pct"] / 100.0, 0.0)

    # Collect normalized scalars
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

    # Compute weighted influence scalar
    influence_scalar = sum(scalars[k] * weights.get(k, 0) for k in scalars)

    # Add influence scalar to result
    scalars["influence_scalar"] = round(influence_scalar, 3)

    # Round all values for better readability
    return {k: round(v, 3) for k, v in scalars.items()}


def classify_activity_level(activity_level: Union[str, ActivityLevel]) -> float:
    """
    Convert activity level to normalized scalar value.

    Args:
        activity_level: Activity level string or enum

    Returns:
        Scalar value between 0 and 1
    """
    # Handle string input
    if isinstance(activity_level, str):
        try:
            # Try to convert to enum
            activity_level = ActivityLevel(activity_level.capitalize())
        except ValueError:
            # Unknown string - return neutral value
            logger.warning(f"Unknown activity level: {activity_level}")
            return 0.5

    # Look up scalar value for this activity level
    return ACTIVITY_SCALAR_MAP.get(activity_level, 0.5)


def calculate_overall_fitness_scalar(
    strength_conditioning_scalar: float,
    activity_level_scalar: float,
    strength_weight: float = 0.6,
    activity_weight: float = 0.4,
) -> float:
    """
    Calculate overall fitness scalar from strength/conditioning and activity level.

    Args:
        strength_conditioning_scalar: Normalized strength/conditioning score
        activity_level_scalar: Normalized activity level score
        strength_weight: Weight factor for strength component
        activity_weight: Weight factor for activity component

    Returns:
        Overall fitness scalar between 0 and 1
    """
    # Validate inputs
    if not (0.0 <= strength_conditioning_scalar <= 1.0):
        raise ValueError("Strength and conditioning scalar must be between 0.0 and 1.0")

    if not (0.0 <= activity_level_scalar <= 1.0):
        raise ValueError("Activity level scalar must be between 0.0 and 1.0")

    # Validate weights sum to 1.0
    if not ((strength_weight >= 0) and (activity_weight >= 0)):
        raise ValueError("Weights must be non-negative")

    weight_sum = strength_weight + activity_weight
    if abs(weight_sum - 1.0) > 0.01:  # Allow small floating-point error
        logger.warning(f"Weights do not sum to 1.0 (sum: {weight_sum}), normalizing")
        strength_weight = strength_weight / weight_sum
        activity_weight = activity_weight / weight_sum

    # Calculate weighted average
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
    Compute and persist the final fitness scalar for a user.

    Steps:
      1. Calculate the influence scalar from performance metrics
      2. Get the user's current activity level
      3. Compute final scalar by combining metrics and activity
      4. Update the user's activity level based on final scalar

    Args:
        user_id: User identifier
        days: Lookback period in days
        strength_weight: Weight for strength/conditioning component
        activity_weight: Weight for activity level component

    Returns:
        Final fitness scalar between 0 and 1
    """
    # 1. Get influence scalar
    scalars = compute_influence_scalars(user_id, days)
    influence = scalars["influence_scalar"]

    # 2. Get current activity level scalar
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT currentActivityLevel FROM users WHERE user_id = ?", (user_id,)
        )
        row = cur.fetchone()

    level = row[0] if row else None
    activity_scalar = classify_activity_level(level) if level else 0.5

    # 3. Calculate final scalar
    final_scalar = calculate_overall_fitness_scalar(
        strength_conditioning_scalar=influence,
        activity_level_scalar=activity_scalar,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )

    # 4. Update user's activity level based on final scalar
    # Map final_scalar to discrete activity level
    if final_scalar >= 0.95:
        new_level = ActivityLevel.INTENSE.value
    elif final_scalar >= 0.8:
        new_level = ActivityLevel.ACTIVE.value
    elif final_scalar >= 0.6:
        new_level = ActivityLevel.MODERATE.value
    elif final_scalar >= 0.3:
        new_level = ActivityLevel.CASUAL.value
    else:
        new_level = ActivityLevel.SEDENTARY.value

    # Persist updated activity level
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET currentActivityLevel = ? WHERE user_id = ?",
            (new_level, user_id),
        )
        conn.commit()

    logger.info(f"Updated activity level for user {user_id} to {new_level}")

    return final_scalar


def classify_overall_fitness_tier(final_scalar: float) -> str:
    """
    Classify fitness scalar into descriptive tiers.

    Args:
        final_scalar: Overall fitness scalar (0-1)

    Returns:
        String tier classification
    """
    if final_scalar >= 0.95:
        return "Elite"  # Top 1% of fitness
    elif final_scalar >= 0.85:
        return "Advanced"  # Top 5% of fitness
    elif final_scalar >= 0.65:
        return "Intermediate"  # Top 25% of fitness
    elif final_scalar >= 0.4:
        return "Novice"  # Average fitness
    else:
        return "Beginner"  # Below average fitness


def calculate_goal_specific_scalars(
    user_id: int, goal_type: str, days: int = 7
) -> Dict[str, float]:
    """
    Calculate goal-specific scaled metrics for tracking and recommendations.

    Args:
        user_id: User identifier
        goal_type: Type of goal
        days: Lookback period in days

    Returns:
        Dictionary of goal-specific normalized metrics
    """
    # Get base metrics
    strength = get_strength_metrics(user_id, days)
    cond = get_conditioning_metrics(user_id, days)

    # Define goal-specific weightings
    weights = {
        "Strength": {
            "combined_strength": 0.5,  # Heavy emphasis on strength
            "intensity_avg": 0.25,  # Focus on intensity
            "total_volume": 0.15,  # Moderate volume
            "consistency_pct": 0.1,  # Some consistency
        },
        "Endurance": {
            "training_days": 0.4,  # Frequency is key
            "weekly_volume": 0.3,  # High volume
            "consistency_pct": 0.2,  # Strong consistency
            "volume_change_pct": 0.1,  # Progressive overload
        },
        "Weight-Loss": {
            "weekly_volume": 0.4,  # Volume is key
            "training_days": 0.3,  # Frequency helps
            "volume_change_pct": 0.2,  # Progressive increase
            "consistency_pct": 0.1,  # Being consistent
        },
        "Performance": {
            "combined_strength": 0.35,  # Strength base
            "intensity_avg": 0.25,  # Focused intensity
            "training_days": 0.2,  # Consistent practice
            "weekly_volume": 0.2,  # Sufficient volume
        },
        "Default": {
            "combined_strength": 0.25,  # Balanced approach
            "weekly_volume": 0.25,  # Balanced approach
            "training_days": 0.25,  # Balanced approach
            "consistency_pct": 0.25,  # Balanced approach
        },
    }

    # Get appropriate weights for this goal
    goal_weights = weights.get(goal_type, weights["Default"])

    # Normalize individual metrics (reusing the same normalization logic)
    normalized = {
        "combined_strength": min(strength["combined_strength"] / 2.0, 1.0),
        "total_volume": min(strength["total_volume"] / 10000.0, 1.0),
        "weekly_volume": min(cond["weekly_volume"] / 20000.0, 1.0),
        "training_days": min(cond["training_days"] / 7.0, 1.0),
        "volume_change_pct": max(
            min((cond["volume_change_pct"] + 100) / 200.0, 1.0), 0.0
        ),
        "intensity_avg": min(cond["intensity_avg"] / 100.0, 1.0),
        "consistency_pct": max(1.0 - cond["consistency_pct"] / 100.0, 0.0),
    }

    # Calculate weighted score for this goal type
    goal_score = sum(normalized.get(k, 0.0) * v for k, v in goal_weights.items())

    # Add goal score to normalized metrics
    normalized["goal_score"] = round(goal_score, 3)

    # Round all values for better readability
    return {k: round(v, 3) for k, v in normalized.items()}


def normalize_intensity(
    user_intensity: float, user_fitness_tier: str
) -> Dict[str, Any]:
    """
    Normalize intensity relative to user's fitness level and provide guidance.

    Args:
        user_intensity: Raw intensity value (e.g., volume/reps)
        user_fitness_tier: User's classified fitness tier

    Returns:
        Dictionary with normalized values and guidance
    """
    # Optimal intensity range by fitness tier (min, max)
    optimal_ranges = {
        "Beginner": (15, 40),
        "Novice": (25, 60),
        "Intermediate": (40, 80),
        "Advanced": (60, 100),
        "Elite": (80, 150),
    }

    # Get range for this user
    min_optimal, max_optimal = optimal_ranges.get(user_fitness_tier, (30, 70))

    # Determine where user falls relative to range
    if user_intensity < min_optimal:
        relative_position = "below"
        pct_from_optimal = (min_optimal - user_intensity) / min_optimal * 100
        guidance = "Consider increasing training intensity for better results"
    elif user_intensity > max_optimal:
        relative_position = "above"
        pct_from_optimal = (user_intensity - max_optimal) / max_optimal * 100
        guidance = "Consider reducing intensity to prevent overtraining"
    else:
        relative_position = "within"
        # Calculate as percentage through the optimal range
        range_width = max_optimal - min_optimal
        pct_from_optimal = (user_intensity - min_optimal) / range_width * 100
        guidance = (
            "Your training intensity is in the optimal range for your fitness level"
        )

    # Normalized value (0-1 scale)
    # Below optimal maps to 0.0-0.4
    # Optimal maps to 0.4-0.8
    # Above optimal maps to 0.8-1.0
    if relative_position == "below":
        normalized_value = 0.4 * (1 - min(pct_from_optimal, 100) / 100)
    elif relative_position == "above":
        normalized_value = 0.8 + (0.2 * min(pct_from_optimal, 100) / 100)
    else:  # within optimal
        normalized_value = 0.4 + (0.4 * pct_from_optimal / 100)

    return {
        "raw_intensity": user_intensity,
        "normalized_value": round(normalized_value, 3),
        "optimal_range": (min_optimal, max_optimal),
        "relative_position": relative_position,
        "percent_from_optimal": round(pct_from_optimal, 1),
        "guidance": guidance,
    }


def volume_progression_guidance(
    current_volume: float, past_volume: float, fitness_tier: str, goal_type: str
) -> Dict[str, Any]:
    """
    Calculate volume progression guidance based on user's goals and fitness level.

    Args:
        current_volume: Current training volume
        past_volume: Previous period training volume
        fitness_tier: User's classified fitness tier
        goal_type: Type of goal

    Returns:
        Dictionary with recommendation and guidance
    """
    # Calculate current progression
    if past_volume > 0:
        current_progression = (current_volume - past_volume) / past_volume * 100
    else:
        current_progression = 0 if current_volume == 0 else 100

    # Optimal weekly progression rates by fitness tier and goal
    progression_rates = {
        "Beginner": {
            "Strength": (5, 10),
            "Endurance": (10, 15),
            "Weight-Loss": (10, 20),
            "Performance": (5, 15),
            "Default": (5, 10),
        },
        "Novice": {
            "Strength": (3, 8),
            "Endurance": (5, 12),
            "Weight-Loss": (5, 15),
            "Performance": (3, 10),
            "Default": (3, 8),
        },
        "Intermediate": {
            "Strength": (2, 5),
            "Endurance": (3, 8),
            "Weight-Loss": (3, 10),
            "Performance": (2, 7),
            "Default": (2, 5),
        },
        "Advanced": {
            "Strength": (1, 3),
            "Endurance": (2, 5),
            "Weight-Loss": (2, 7),
            "Performance": (1, 4),
            "Default": (1, 3),
        },
        "Elite": {
            "Strength": (0.5, 2),
            "Endurance": (1, 3),
            "Weight-Loss": (1, 4),
            "Performance": (0.5, 2),
            "Default": (0.5, 2),
        },
    }

    # Get optimal rates for this user
    tier_rates = progression_rates.get(fitness_tier, progression_rates["Intermediate"])
    min_optimal, max_optimal = tier_rates.get(goal_type, tier_rates["Default"])

    # Determine guidance
    if current_progression < min_optimal:
        status = "below_optimal"
        message = f"Your training volume is increasing too slowly for optimal {goal_type.lower()} progression."
        suggestion = (
            f"Consider increasing weekly volume by {min_optimal}% to {max_optimal}%."
        )
    elif current_progression > max_optimal * 1.5:  # Well above optimal
        status = "excessive"
        message = f"Your training volume is increasing too rapidly, which may lead to overtraining or injury."
        suggestion = f"Consider slowing down to {min_optimal}% to {max_optimal}% weekly increases."
    elif current_progression > max_optimal:  # Above optimal but not excessive
        status = "above_optimal"
        message = f"Your training volume is increasing faster than optimal for {goal_type.lower()}."
        suggestion = f"This may be sustainable short-term, but consider targeting {min_optimal}% to {max_optimal}% increases."
    else:  # Within optimal range
        status = "optimal"
        message = f"Your training volume progression is optimal for your {goal_type.lower()} goals."
        suggestion = f"Continue with your current approach, aiming for {min_optimal}% to {max_optimal}% weekly increases."

    # Calculate recommended volume for next week
    recommended_min = current_volume * (1 + min_optimal / 100)
    recommended_max = current_volume * (1 + max_optimal / 100)

    return {
        "current_progression": round(current_progression, 1),
        "optimal_range": (min_optimal, max_optimal),
        "status": status,
        "message": message,
        "suggestion": suggestion,
        "recommended_range": (round(recommended_min, 0), round(recommended_max, 0)),
    }
