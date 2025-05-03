import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import date, datetime, timedelta

from backend.database.db import create_conn
from backend.models.models import GoalType, StrengthDimension, ConditioningDimension
from backend.engines.scalars import (
    compute_influence_scalars,
    compute_final_scalar,
    classify_overall_fitness_tier,
)


def initialize_target_vector(
    user_id: int,
    goal_type: GoalType,
    target_date: date,
    profile_name: str = "default",
    custom_dimensions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Initialize a target vector based on the user's goal type and target date.

    Steps:
      1. Get user's current vector as baseline
      2. Apply goal-specific adjustments to create target
      3. Calculate intermediate milestone vectors based on time to target
      4. Persist target vector into target_profile table

    Parameters:
        user_id (int): User ID
        goal_type (GoalType): Type of fitness goal
        target_date (date): Date to reach the target
        profile_name (str): Name for this target profile
        custom_dimensions (Dict[str, float], optional): Custom dimension values

    Returns:
        Dict with 'dimensions' (List[str]), 'vector' (List[float]), and other details
    """
    # 1) Get current user vector as baseline
    current_vector = _get_current_user_vector(user_id, profile_name)

    if not current_vector:
        raise ValueError(
            f"User vector not found for user_id={user_id}, profile={profile_name}"
        )

    # Extract the vector details
    dimensions = current_vector["dimensions"]
    baseline_values = current_vector["vector"]

    # 2) Apply adjustments based on goal_type to create target
    target_values = _apply_goal_adjustments(
        dimensions, baseline_values, goal_type, custom_dimensions
    )

    # 3) Calculate milestone vectors between now and target date
    milestones = _calculate_milestone_vectors(
        dimensions, baseline_values, target_values, target_date
    )

    # 4) Persist target vector
    target_id = _persist_target_vector(
        user_id,
        profile_name,
        goal_type,
        target_date,
        dimensions,
        target_values,
        milestones,
    )

    # 5) Return full target details
    return {
        "target_id": target_id,
        "user_id": user_id,
        "goal_type": goal_type,
        "profile_name": profile_name,
        "target_date": target_date,
        "dimensions": dimensions,
        "vector": target_values,
        "milestones": milestones,
    }


def _get_current_user_vector(
    user_id: int, profile_name: str = "default"
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the current user vector from the database.

    Returns None if not found.
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
        return None

    # Parse the comma-separated dimensions and vector values
    dimensions = row[0].split(",") if row[0] else []
    vector_str = row[1].split(",") if row[1] else []
    vector = [float(v) for v in vector_str]
    created_at = row[2]

    return {"dimensions": dimensions, "vector": vector, "created_at": created_at}


def _apply_goal_adjustments(
    dimensions: List[str],
    baseline_values: List[float],
    goal_type: GoalType,
    custom_dimensions: Optional[Dict[str, float]] = None,
) -> List[float]:
    """
    Apply goal-specific adjustments to create a target vector.

    Different goals will emphasize different metrics:
      - STRENGTH: Emphasizes strength dimensions
      - ENDURANCE: Emphasizes volume and consistency
      - WEIGHT_LOSS: Balanced approach with focus on volume
      - PERFORMANCE: Emphasizes intensity and consistency

    Returns a new vector with adjusted values.
    """
    # Start with a copy of the baseline
    target_values = baseline_values.copy()

    # Create a mapping of dimension names to indices
    dim_to_idx = {dim: i for i, dim in enumerate(dimensions)}

    # Define goal-specific improvement factors
    # Values represent target improvements:
    # 0.0 = no change, 0.2 = 20% improvement, etc.
    improvement_map = {
        GoalType.STRENGTH: {
            "combined_strength": 0.3,  # 30% strength improvement
            "total_volume": 0.2,  # 20% volume increase
            "intensity_avg": 0.25,  # 25% intensity increase
            "influence_scalar": 0.2,  # 20% overall influence improvement
        },
        GoalType.ENDURANCE: {
            "weekly_volume": 0.4,  # 40% volume increase
            "consistency_pct": 0.3,  # 30% consistency improvement
            "training_days": 0.3,  # 30% more training days
        },
        GoalType.WEIGHT_LOSS: {
            "weekly_volume": 0.5,  # 50% volume increase
            "training_days": 0.4,  # 40% more training days
            "intensity_avg": 0.1,  # 10% intensity increase
        },
        GoalType.PERFORMANCE: {
            "combined_strength": 0.2,  # 20% strength improvement
            "weekly_volume": 0.3,  # 30% volume increase
            "intensity_avg": 0.3,  # 30% intensity increase
            "consistency_pct": 0.4,  # 40% consistency improvement
        },
        GoalType.DEFAULT: {
            "combined_strength": 0.15,  # 15% strength improvement
            "weekly_volume": 0.15,  # 15% volume increase
            "training_days": 0.15,  # 15% more training days
        },
    }

    # Get the appropriate improvement factors for this goal type
    improvements = improvement_map.get(goal_type, improvement_map[GoalType.DEFAULT])

    # Apply improvements to the baseline values
    for dim, factor in improvements.items():
        if dim in dim_to_idx:
            idx = dim_to_idx[dim]
            # The improvement is relative to the current value, but capped at 1.0
            target_values[idx] = min(baseline_values[idx] * (1 + factor), 1.0)

    # Override with any custom dimension values
    if custom_dimensions:
        for dim, value in custom_dimensions.items():
            if dim in dim_to_idx:
                idx = dim_to_idx[dim]
                # Ensure custom values are within valid range [0.0, 1.0]
                target_values[idx] = max(0.0, min(value, 1.0))

    # Calculate final_scalar directly as the last element if it exists
    if "final_scalar" in dim_to_idx:
        final_idx = dim_to_idx["final_scalar"]
        # Ensure final_scalar is the weighted sum of the contributing factors
        # This is a simple approximation - in practice you might want to use
        # the actual calculation from compute_final_scalar
        target_values[final_idx] = min(
            baseline_values[final_idx] * 1.25,  # 25% improvement cap
            0.98,  # Cap at 0.98 as 1.0 is considered "perfect"
        )

    return target_values


def _calculate_milestone_vectors(
    dimensions: List[str],
    baseline_values: List[float],
    target_values: List[float],
    target_date: date,
) -> List[Dict[str, Any]]:
    """
    Calculate intermediate milestone vectors between baseline and target.

    Creates milestone vectors at 25%, 50%, and 75% progress points.

    Returns a list of milestone dictionaries with date and vector values.
    """
    # Calculate the total number of days to target
    today = date.today()
    total_days = (target_date - today).days

    if total_days <= 0:
        # Target date is today or in the past, no milestones needed
        return []

    milestones = []

    # Create milestones at 25%, 50%, and 75% time points
    for percent in [0.25, 0.5, 0.75]:
        # Calculate the date for this milestone
        milestone_days = int(total_days * percent)
        milestone_date = today + timedelta(days=milestone_days)

        # Calculate interpolated vector values
        milestone_values = []
        for i in range(len(baseline_values)):
            # Linear interpolation between baseline and target
            value = (
                baseline_values[i] + (target_values[i] - baseline_values[i]) * percent
            )
            milestone_values.append(round(value, 3))

        milestones.append(
            {
                "percent": int(percent * 100),
                "date": milestone_date.isoformat(),
                "vector": milestone_values,
            }
        )

    return milestones


def _persist_target_vector(
    user_id: int,
    profile_name: str,
    goal_type: GoalType,
    target_date: date,
    dimensions: List[str],
    vector: List[float],
    milestones: List[Dict[str, Any]],
) -> int:
    """
    Persist the target vector and milestones to the database.

    Returns the target_id.
    """
    # Convert lists to comma-separated strings
    dims_str = ",".join(dimensions)
    vec_str = ",".join(f"{v:.3f}" for v in vector)

    # Convert milestones to JSON-like string for storage
    # In production you might want to use actual JSON or a separate table
    milestone_str = "|".join(
        f"{m['percent']}:{m['date']}:{','.join(f'{v:.3f}' for v in m['vector'])}"
        for m in milestones
    )

    with create_conn() as conn:
        cur = conn.cursor()
        # ensure table exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS target_profile (
                target_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_name TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                target_date TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                vector TEXT NOT NULL,
                milestones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )
        cur.execute(
            """
            INSERT INTO target_profile (
                user_id, profile_name, goal_type, target_date, 
                dimensions, vector, milestones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                profile_name,
                goal_type.value if isinstance(goal_type, GoalType) else goal_type,
                (
                    target_date.isoformat()
                    if isinstance(target_date, date)
                    else target_date
                ),
                dims_str,
                vec_str,
                milestone_str,
            ),
        )
        conn.commit()
        return cur.lastrowid


def get_target_vector(target_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a target vector by ID.

    Returns None if not found.
    """
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT user_id, profile_name, goal_type, target_date, 
                   dimensions, vector, milestones, created_at
            FROM target_profile
            WHERE target_id = ?
            """,
            (target_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    # Parse the stored data
    (
        user_id,
        profile_name,
        goal_type,
        target_date_str,
        dims_str,
        vec_str,
        milestones_str,
        created_at,
    ) = row

    dimensions = dims_str.split(",")
    vector = [float(v) for v in vec_str.split(",")]

    # Parse milestones string back into list of dicts
    milestones = []
    if milestones_str:
        for milestone in milestones_str.split("|"):
            parts = milestone.split(":")
            if len(parts) >= 3:
                percent = int(parts[0])
                milestone_date = parts[1]
                milestone_vector = [float(v) for v in parts[2].split(",")]
                milestones.append(
                    {
                        "percent": percent,
                        "date": milestone_date,
                        "vector": milestone_vector,
                    }
                )

    return {
        "target_id": target_id,
        "user_id": user_id,
        "profile_name": profile_name,
        "goal_type": goal_type,
        "target_date": target_date_str,
        "dimensions": dimensions,
        "vector": vector,
        "milestones": milestones,
        "created_at": created_at,
    }


def get_user_targets(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all target vectors for a user.

    Returns a list of target summaries (without full vector details).
    """
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT target_id, profile_name, goal_type, target_date, created_at
            FROM target_profile
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()

    targets = []
    for row in rows:
        target_id, profile_name, goal_type, target_date_str, created_at = row

        # Calculate progress percentage
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            today = date.today()
            start_date = datetime.strptime(created_at.split()[0], "%Y-%m-%d").date()

            total_days = (target_date - start_date).days
            days_passed = (today - start_date).days

            if total_days <= 0:
                progress_pct = 100.0
            else:
                progress_pct = min(100.0, max(0.0, days_passed / total_days * 100.0))
        except (ValueError, AttributeError):
            progress_pct = 0.0

        targets.append(
            {
                "target_id": target_id,
                "profile_name": profile_name,
                "goal_type": goal_type,
                "target_date": target_date_str,
                "progress_pct": round(progress_pct, 1),
                "created_at": created_at,
            }
        )

    return targets


def get_current_milestone(target_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the current milestone for a target based on today's date.

    Returns the milestone that's closest to today without exceeding it.
    If today is past all milestones, returns the final target.
    """
    target = get_target_vector(target_id)
    if not target:
        return None

    today = date.today()
    target_date = datetime.strptime(target["target_date"], "%Y-%m-%d").date()

    # If we're already at or past the target date, return the full target
    if today >= target_date:
        return {
            "percent": 100,
            "date": target["target_date"],
            "vector": target["vector"],
            "is_final": True,
        }

    # Check each milestone to find the current one
    milestones = target["milestones"]
    current_milestone = None

    for milestone in milestones:
        milestone_date = datetime.strptime(milestone["date"], "%Y-%m-%d").date()

        if today >= milestone_date:
            # This milestone has been reached
            if (
                current_milestone is None
                or milestone["percent"] > current_milestone["percent"]
            ):
                current_milestone = milestone
        elif current_milestone is None:
            # We haven't reached the first milestone yet, so use a pro-rated initial milestone
            start_date = datetime.strptime(
                target["created_at"].split()[0], "%Y-%m-%d"
            ).date()
            total_days = (target_date - start_date).days
            days_passed = (today - start_date).days

            if total_days > 0:
                percent = days_passed / total_days * 100

                # Pro-rate between baseline and first milestone
                baseline_vector = _get_current_user_vector(target["user_id"])["vector"]
                first_milestone = milestones[0]
                first_milestone_percent = first_milestone["percent"] / 100

                # Interpolate between baseline and first milestone
                pro_rated_vector = []
                for i in range(len(baseline_vector)):
                    pro_rated_value = baseline_vector[i] + (
                        first_milestone["vector"][i] - baseline_vector[i]
                    ) * (percent / first_milestone["percent"])
                    pro_rated_vector.append(round(pro_rated_value, 3))

                current_milestone = {
                    "percent": round(percent, 1),
                    "date": today.isoformat(),
                    "vector": pro_rated_vector,
                    "is_prorated": True,
                }
                break

    # If no milestone has been reached, return a 0% milestone
    if current_milestone is None:
        baseline_vector = _get_current_user_vector(target["user_id"])["vector"]
        current_milestone = {
            "percent": 0,
            "date": today.isoformat(),
            "vector": baseline_vector,
            "is_initial": True,
        }

    return current_milestone


def calculate_goal_progress(user_id: int, target_id: int) -> Dict[str, Any]:
    """
    Calculate the user's progress toward a specific target.

    Compares the user's current vector against the current milestone
    and the final target to determine progress metrics.

    Returns a dictionary with progress details.
    """
    # Get the target details
    target = get_target_vector(target_id)
    if not target:
        raise ValueError(f"Target not found: target_id={target_id}")

    # Get the current user vector
    current_vector = _get_current_user_vector(user_id)
    if not current_vector:
        raise ValueError(f"User vector not found for user_id={user_id}")

    # Get the current milestone
    current_milestone = get_current_milestone(target_id)

    # Calculate time-based progress
    today = date.today()
    start_date = datetime.strptime(target["created_at"].split()[0], "%Y-%m-%d").date()
    target_date = datetime.strptime(target["target_date"], "%Y-%m-%d").date()

    total_days = (target_date - start_date).days
    days_passed = (today - start_date).days
    days_remaining = max(0, (target_date - today).days)

    time_progress_pct = (
        min(100.0, max(0.0, days_passed / total_days * 100.0))
        if total_days > 0
        else 100.0
    )

    # Calculate vector-based progress
    vector_progress = []
    overall_progress = 0.0
    progress_count = 0

    # Compare current values to target values for each dimension
    for i, dim in enumerate(target["dimensions"]):
        if i < len(current_vector["vector"]):
            current_val = current_vector["vector"][i]
            target_val = target["vector"][i]
            start_val = _get_current_user_vector(user_id)["vector"][
                i
            ]  # Original baseline

            # Don't divide by zero
            if target_val == start_val:
                progress_pct = 100.0 if current_val >= target_val else 0.0
            else:
                progress_pct = min(
                    100.0,
                    max(
                        0.0,
                        (current_val - start_val) / (target_val - start_val) * 100.0,
                    ),
                )

            vector_progress.append(
                {
                    "dimension": dim,
                    "current": round(current_val, 3),
                    "target": round(target_val, 3),
                    "progress_pct": round(progress_pct, 1),
                }
            )

            # Only include key dimensions in overall progress
            if dim in [
                "combined_strength",
                "weekly_volume",
                "training_days",
                "intensity_avg",
                "consistency_pct",
                "final_scalar",
            ]:
                overall_progress += progress_pct
                progress_count += 1

    # Calculate overall progress as average of key dimensions
    overall_progress_pct = (
        round(overall_progress / progress_count, 1) if progress_count > 0 else 0.0
    )

    # Compare to time-based expectation
    on_track = (
        overall_progress_pct >= time_progress_pct * 0.8
    )  # 80% of expected is "on track"

    return {
        "target_id": target_id,
        "goal_type": target["goal_type"],
        "time_progress_pct": round(time_progress_pct, 1),
        "vector_progress_pct": overall_progress_pct,
        "on_track": on_track,
        "days_passed": days_passed,
        "days_remaining": days_remaining,
        "total_days": total_days,
        "current_milestone_pct": (
            current_milestone["percent"] if current_milestone else 0
        ),
        "dimension_progress": vector_progress,
        "target_date": target["target_date"],
    }
