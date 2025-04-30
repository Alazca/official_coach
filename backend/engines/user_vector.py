import numpy as np
from typing import Dict, List, Any

from backend.database.db import create_conn
from backend.engines.scalars import (
    classify_overall_fitness_tier,
    compute_final_scalar,
    compute_influence_scalars,
)


def initialize_user_vector(
    user_id: int,
    profile_name: str = "default",
    days: int = 7,
    strength_weight: float = 0.6,
    activity_weight: float = 0.4,
) -> Dict[str, Any]:
    """
    Initialize the user's vector based on scalar influence and activity level.

    Steps:
      1. Compute all influence scalars (dict of normalized metrics + 'influence_scalar').
      2. Compute the final fitness scalar by blending with activity level.
      3. Build dimensions list and vector values.
      4. Persist into user_profile table (comma-separated TEXT).

    Returns:
      Dict with 'dimensions' (List[str]) and 'vector' (List[float]).
    """
    # 1) Influence scalars
    scalars = compute_influence_scalars(user_id, days)

    # 2) Final fitness scalar
    final_scalar = compute_final_scalar(
        user_id=user_id,
        days=days,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )

    # 3) Build user-vector
    dimensions: List[str] = list(scalars.keys()) + ["final_scalar"]
    vector: List[float] = [scalars[k] for k in scalars] + [final_scalar]

    # Convert lists to comma-separated strings
    dims_str = ",".join(dimensions)
    vec_str = ",".join(f"{v:.3f}" for v in vector)

    # 4) Persist into user_profile
    with create_conn() as conn:
        cur = conn.cursor()
        # ensure table exists
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
        cur.execute(
            """
            INSERT INTO user_profile (user_id, name, dimensions, vector)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, name) DO UPDATE SET
              dimensions = excluded.dimensions,
              vector     = excluded.vector,
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

    return {
        "dimensions": dimensions,
        "vector": vector,
    }


def update_user_vector(
    user_id: int,
    profile_name: str = "default",
    days: int = 7,
    strength_weight: float = 0.6,
    activity_weight: float = 0.4,
) -> Dict[str, Any]:
    """
    Recompute and update the user's vector and activity level.

    Returns dict including:
      - 'dimensions': List[str]
      - 'vector': List[float]
      - 'influence_scalars': Dict[str, float]
      - 'final_scalar': float
      - 'activity_level': str
    """
    # 1) Initialize and persist vector
    result = initialize_user_vector(
        user_id=user_id,
        profile_name=profile_name,
        days=days,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )

    # 2) Retrieve computed scalars
    influence_scalars = compute_influence_scalars(user_id, days)
    final_scalar = compute_final_scalar(
        user_id=user_id,
        days=days,
        strength_weight=strength_weight,
        activity_weight=activity_weight,
    )

    # 3) Determine activity level from final_scalar
    activity_level = classify_overall_fitness_tier(final_scalar)

    # 4) Merge into result and return
    result.update(
        {
            "influence_scalars": influence_scalars,
            "final_scalar": final_scalar,
            "activity_level": activity_level,
        }
    )
    return result
