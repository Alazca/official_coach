import numpy as np
import logging

from typing import Dict, List, Any, Optional

from backend.database.db import create_conn
from backend.models.models import UserVector
from backend.engines.scalars import (
    classify_overall_fitness_tier,
    compute_final_scalar,
    compute_influence_scalars,
)

# Configure logger
logger = logging.getLogger(__name__)


def initialize_user_vector(
    user_id: int,
    profile_name: str = "default",
    days: int = 7,
    strength_weight: float = 0.6,
    activity_weight: float = 0.4,
) -> UserVector:
    """
    Create a new user vector based on performance metrics and activity level.

    Steps:
    1. Compute normalized influence scalars from performance metrics
    2. Compute final fitness scalar using activity level
    3. Build vector representation with all components
    4. Persist to database for future reference

    Args:
        user_id: User identifier
        profile_name: Name for this vector profile
        days: Lookback period in days for metrics calculation
        strength_weight: Weight factor for strength component
        activity_weight: Weight factor for activity component

    Returns:
        UserVector object with complete vector information
    """
    # 1. Calculate influence scalars
    scalars = compute_influence_scalars(user_id, days)

    # 2. Calculate final fitness scalar
    final_scalar = compute_final_scalar(
        user_id=user_id,
        days=days,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )

    # 3. Build user vector
    dimensions: List[str] = list(scalars.keys()) + ["final_scalar"]
    vector: List[float] = [scalars[k] for k in scalars] + [final_scalar]

    # Convert lists to comma-separated strings for storage
    dims_str = ",".join(dimensions)
    vec_str = ",".join(f"{v:.3f}" for v in vector)

    # 4. Persist to database
    with create_conn() as conn:
        cur = conn.cursor()
        # Ensure table exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                vector TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, name)
            )
            """
        )

        # Insert or update vector
        cur.execute(
            """
            INSERT INTO user_profile (user_id, name, dimensions, vector)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, name) DO UPDATE SET
                dimensions = excluded.dimensions,
                vector = excluded.vector,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                profile_name,
                dims_str,
                vec_str,
            ),
        )
        conn.commit()

    # 5. Create and return user vector object
    return UserVector(
        user_id=user_id,
        profile_name=profile_name,
        dimensions=dimensions,
        vector=vector,
        activity_level=classify_overall_fitness_tier(final_scalar),
        final_scalar=final_scalar,
        influence_scalars=scalars,
    )


def get_user_vector(
    user_id: int, profile_name: str = "default"
) -> Optional[UserVector]:
    """
    Retrieve user vector from database.

    Args:
        user_id: User identifier
        profile_name: Name of vector profile to retrieve

    Returns:
        UserVector object if found, None otherwise
    """
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT dimensions, vector, created_at 
            FROM user_profile 
            WHERE user_id = ? AND name = ?
            """,
            (user_id, profile_name),
        )
        row = cur.fetchone()

    if not row:
        logger.warning(
            f"No user vector found for user {user_id}, profile {profile_name}"
        )
        return None

    # Parse stored data
    dimensions = row[0].split(",") if row[0] else []
    vector_str = row[1].split(",") if row[1] else []
    vector = [float(v) for v in vector_str]
    created_at = row[2]

    # Get final scalar if present
    final_scalar = vector[-1] if "final_scalar" in dimensions else None

    # Map dimensions to values for influence scalars
    influence_scalars = {
        dim: vec for dim, vec in zip(dimensions, vector) if dim != "final_scalar"
    }

    # Determine fitness level
    activity_level = (
        classify_overall_fitness_tier(final_scalar) if final_scalar else None
    )

    return UserVector(
        user_id=user_id,
        profile_name=profile_name,
        dimensions=dimensions,
        vector=vector,
        created_at=created_at,
        activity_level=activity_level,
        final_scalar=final_scalar,
        influence_scalars=influence_scalars,
    )


def update_user_vector(
    user_id: int,
    profile_name: str = "default",
    days: int = 7,
    strength_weight: float = 0.6,
    activity_weight: float = 0.4,
) -> UserVector:
    """
    Recompute and update user vector with current metrics.

    Args:
        user_id: User identifier
        profile_name: Name of vector profile
        days: Lookback period in days
        strength_weight: Weight for strength component
        activity_weight: Weight for activity component

    Returns:
        Updated UserVector object
    """
    return initialize_user_vector(
        user_id=user_id,
        profile_name=profile_name,
        days=days,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )


def get_user_vector_history(
    user_id: int, profile_name: str = "default", days: int = 90
) -> List[Dict[str, Any]]:
    """
    Retrieve historical user vectors to track progress over time.

    Args:
        user_id: User identifier
        profile_name: Name of vector profile
        days: Maximum lookback period in days

    Returns:
        List of historical vector snapshots
    """
    # Get date threshold
    today = date.today()
    start_date = (today - timedelta(days=days)).isoformat()

    with create_conn() as conn:
        cur = conn.cursor()
        # Check if history table exists, create if not
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_vector_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_name TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                vector TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        # Get historical records
        cur.execute(
            """
            SELECT dimensions, vector, snapshot_date, created_at
            FROM user_vector_history 
            WHERE user_id = ? AND profile_name = ? AND snapshot_date >= ?
            ORDER BY snapshot_date ASC
            """,
            (user_id, profile_name, start_date),
        )
        rows = cur.fetchall()

    history = []
    for row in rows:
        dimensions = row[0].split(",") if row[0] else []
        vector_str = row[1].split(",") if row[1] else []
        vector = [float(v) for v in vector_str]
        snapshot_date = row[2]
        created_at = row[3]

        history.append(
            {
                "dimensions": dimensions,
                "vector": vector,
                "snapshot_date": snapshot_date,
                "created_at": created_at,
                "vector_dict": vector_to_dict(np.array(vector), dimensions),
            }
        )

    return history


def save_vector_snapshot(user_id: int, profile_name: str = "default") -> bool:
    """
    Save current user vector as a snapshot in history table.

    Args:
        user_id: User identifier
        profile_name: Name of vector profile

    Returns:
        True if snapshot was saved successfully
    """
    # Get current vector
    user_vector = get_user_vector(user_id, profile_name)
    if not user_vector:
        logger.warning(f"Cannot save snapshot - no vector found for user {user_id}")
        return False

    # Convert to storage format
    dims_str = ",".join(user_vector.dimensions)
    vec_str = ",".join(f"{v:.3f}" for v in user_vector.vector)
    today = date.today().isoformat()

    with create_conn() as conn:
        cur = conn.cursor()
        # Ensure history table exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_vector_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_name TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                vector TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        # Check if we already have a snapshot for today
        cur.execute(
            """
            SELECT COUNT(*)
            FROM user_vector_history
            WHERE user_id = ? AND profile_name = ? AND snapshot_date = ?
            """,
            (user_id, profile_name, today),
        )

        count = cur.fetchone()[0]

        if count > 0:
            # Update existing snapshot
            cur.execute(
                """
                UPDATE user_vector_history
                SET dimensions = ?, vector = ?, created_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND profile_name = ? AND snapshot_date = ?
                """,
                (dims_str, vec_str, user_id, profile_name, today),
            )
        else:
            # Insert new snapshot
            cur.execute(
                """
                INSERT INTO user_vector_history
                (user_id, profile_name, dimensions, vector, snapshot_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, profile_name, dims_str, vec_str, today),
            )

        conn.commit()

    return True


def analyze_vector_trends(
    user_id: int, profile_name: str = "default", days: int = 90
) -> Dict[str, Any]:
    """
    Analyze trends in user vector over time.

    Args:
        user_id: User identifier
        profile_name: Name of vector profile
        days: Lookback period in days

    Returns:
        Dictionary with trend analysis
    """
    # Get vector history
    history = get_user_vector_history(user_id, profile_name, days)
    if not history:
        logger.warning(f"No vector history found for user {user_id}")
        return {
            "trends": {},
            "overall_progress": 0,
            "key_improvements": [],
            "areas_for_growth": [],
        }

    # Need at least two points for trend analysis
    if len(history) < 2:
        logger.info(
            f"Insufficient history for trend analysis ({len(history)} snapshots)"
        )
        return {
            "trends": {},
            "overall_progress": 0,
            "key_improvements": [],
            "areas_for_growth": [],
        }

    # Extract key dimensions to analyze
    key_dimensions = [
        "combined_strength",
        "training_days",
        "weekly_volume",
        "consistency_pct",
        "intensity_avg",
        "final_scalar",
    ]

    # Get the available dimensions from the history
    available_dimensions = set(history[0]["dimensions"])
    analysis_dimensions = [d for d in key_dimensions if d in available_dimensions]

    # Calculate trends
    first_snapshot = history[0]
    latest_snapshot = history[-1]

    trends = {}
    key_improvements = []
    areas_for_growth = []

    for dim in analysis_dimensions:
        try:
            first_idx = first_snapshot["dimensions"].index(dim)
            latest_idx = latest_snapshot["dimensions"].index(dim)

            first_value = first_snapshot["vector"][first_idx]
            latest_value = latest_snapshot["vector"][latest_idx]

            if first_value > 0:
                change_pct = ((latest_value - first_value) / first_value) * 100
            else:
                change_pct = 100 if latest_value > 0 else 0

            trends[dim] = {
                "first_value": first_value,
                "latest_value": latest_value,
                "change_pct": round(change_pct, 1),
                "trend": (
                    "improving"
                    if change_pct > 5
                    else "declining" if change_pct < -5 else "stable"
                ),
            }

            # Identify key improvements and areas for growth
            if change_pct >= 10:
                key_improvements.append(
                    {"dimension": dim, "change_pct": round(change_pct, 1)}
                )
            elif change_pct <= -5:
                areas_for_growth.append(
                    {"dimension": dim, "change_pct": round(change_pct, 1)}
                )
        except (ValueError, IndexError):
            logger.warning(f"Dimension {dim} not found in vector history")

    # Calculate overall progress (based on final_scalar)
    if "final_scalar" in trends:
        overall_progress = trends["final_scalar"]["change_pct"]
    else:
        # Use average of all trends as fallback
        trend_values = [t["change_pct"] for t in trends.values()]
        overall_progress = sum(trend_values) / len(trend_values) if trend_values else 0

    return {
        "trends": trends,
        "overall_progress": round(overall_progress, 1),
        "key_improvements": sorted(
            key_improvements, key=lambda x: x["change_pct"], reverse=True
        ),
        "areas_for_growth": sorted(areas_for_growth, key=lambda x: x["change_pct"]),
    }


def get_vector_dimension_info(dimension: str) -> Dict[str, Any]:
    """
    Get description and interpretation guidance for vector dimensions.

    Args:
        dimension: Name of vector dimension

    Returns:
        Dictionary with dimension information
    """
    # Define dimension descriptions and interpretation
    dimension_info = {
        "combined_strength": {
            "title": "Relative Strength",
            "description": "Ratio of lift weights to bodyweight across major lifts",
            "interpretation": {
                "low": "Strength is significantly below potential",
                "medium": "Moderate strength relative to bodyweight",
                "high": "Excellent strength-to-weight ratio",
            },
            "suggested_focus": "Increase intensity in primary strength lifts",
        },
        "total_volume": {
            "title": "Total Work Volume",
            "description": "Total weight moved across all exercises",
            "interpretation": {
                "low": "Low overall training stimulus",
                "medium": "Moderate training volume",
                "high": "High training stimulus",
            },
            "suggested_focus": "Gradually increase sets, reps, or weight",
        },
        "volume_percentile": {
            "title": "Volume Ranking",
            "description": "How your volume compares to other users",
            "interpretation": {
                "low": "Lower volume than most users",
                "medium": "Average training volume",
                "high": "Higher volume than most users",
            },
            "suggested_focus": "Balance volume with recovery capacity",
        },
        "weekly_volume": {
            "title": "Weekly Volume",
            "description": "Training volume over past week",
            "interpretation": {
                "low": "Light training week",
                "medium": "Moderate weekly stimulus",
                "high": "High weekly training load",
            },
            "suggested_focus": "Maintain consistent weekly progression",
        },
        "training_days": {
            "title": "Training Frequency",
            "description": "Number of days with recorded workouts",
            "interpretation": {
                "low": "Infrequent training",
                "medium": "Regular training schedule",
                "high": "High training frequency",
            },
            "suggested_focus": "Find optimal frequency for recovery and progress",
        },
        "volume_change_pct": {
            "title": "Volume Progression",
            "description": "Rate of change in training volume",
            "interpretation": {
                "low": "Stagnant or decreasing volume",
                "medium": "Steady progressive overload",
                "high": "Rapid volume increase",
            },
            "suggested_focus": "Aim for sustainable 5-10% weekly progression",
        },
        "intensity_avg": {
            "title": "Training Intensity",
            "description": "Average weight per rep across exercises",
            "interpretation": {
                "low": "Low intensity training",
                "medium": "Moderate weight intensity",
                "high": "High intensity loading",
            },
            "suggested_focus": "Balance intensity with appropriate volume",
        },
        "consistency_pct": {
            "title": "Training Consistency",
            "description": "Consistency of volume across sessions",
            "interpretation": {
                "low": "Highly variable training loads",
                "medium": "Moderately consistent training",
                "high": "Very consistent training pattern",
            },
            "suggested_focus": "Develop systematic training structure",
        },
        "final_scalar": {
            "title": "Overall Fitness Score",
            "description": "Combined score across all fitness dimensions",
            "interpretation": {
                "low": "Beginner to novice fitness level",
                "medium": "Intermediate fitness level",
                "high": "Advanced to elite fitness level",
            },
            "suggested_focus": "Target weakest dimensions for balanced development",
        },
    }

    # Return info for requested dimension or generic response
    return dimension_info.get(
        dimension,
        {
            "title": dimension.replace("_", " ").title(),
            "description": "Performance metric for fitness assessment",
            "interpretation": {
                "low": "Below target for optimal performance",
                "medium": "Moderate level of performance",
                "high": "High level of performance",
            },
            "suggested_focus": "Progressive improvement through consistent training",
        },
    )
