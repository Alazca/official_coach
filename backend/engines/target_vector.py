"""
Target Vector Module for AI Weightlifting Assistant.

This module provides comprehensive functionality for creating, updating, and analyzing
target vectors that represent fitness goals. It handles goal-specific adjustments,
milestone creation, progress tracking, and goal recommendations.

A target vector exists in the same dimensional space as a user vector, allowing for
direct mathematical comparison between current fitness state and desired outcomes.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, cast
from datetime import date, datetime, timedelta
import logging

from backend.database.db import create_conn
from backend.models.models import (
    GoalType,
    StrengthDimension,
    ConditioningDimension,
    TargetVector,
    MilestoneVector,
)
from backend.engines.scalars import (
    compute_influence_scalars,
    compute_final_scalar,
    classify_overall_fitness_tier,
)
from backend.engines.base_vector_math import (
    weighted_similarity,
)
from backend.engines.user_vector import get_user_vector

# Configure logger
logger = logging.getLogger(__name__)


def initialize_target_vector(
    user_id: int,
    goal_type: Union[GoalType, str],
    target_date: Union[date, str],
    profile_name: str = "default",
    custom_dimensions: Optional[Dict[str, float]] = None,
    description: Optional[str] = None,
) -> Optional[TargetVector]:
    """
    Create a new target vector based on the user's goal type and target date.

    Steps:
    1. Get user's current vector as baseline
    2. Apply goal-specific adjustments to create target
    3. Calculate intermediate milestone vectors
    4. Persist to database for future reference

    Args:
        user_id: User identifier
        goal_type: Type of fitness goal
        target_date: Date to reach the target
        profile_name: Name for this target profile
        custom_dimensions: Optional custom dimension values
        description: Optional goal description

    Returns:
        TargetVector object with complete vector information
    """
    # Convert goal_type to enum if string
    if isinstance(goal_type, str):
        try:
            goal_type = GoalType(goal_type)
        except ValueError:
            logger.warning(f"Invalid goal type: {goal_type}, using DEFAULT")
            goal_type = GoalType.DEFAULT

    # Convert target_date to date object if string
    if isinstance(target_date, str):
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid target date format: {target_date}")
            return None

    # Validate target date is in the future
    if target_date <= date.today():
        logger.error(f"Target date must be in the future: {target_date}")
        return None

    # 1. Get current user vector as baseline
    user_vector = get_user_vector(user_id, profile_name)
    if not user_vector:
        logger.error(
            f"User vector not found for user_id={user_id}, profile={profile_name}"
        )
        return None

    # Extract dimensions and baseline values
    dimensions = user_vector.dimensions
    baseline_values = user_vector.vector

    # 2. Apply goal-specific adjustments
    target_values = _apply_goal_adjustments(
        dimensions, baseline_values, goal_type, custom_dimensions
    )

    # 3. Calculate milestone vectors
    milestones = _calculate_milestone_vectors(
        dimensions, baseline_values, target_values, target_date
    )

    # 4. Create goal description if not provided
    if not description:
        description = _generate_goal_description(
            user_id, goal_type, target_date, user_vector.activity_level
        )

    # 5. Persist target vector
    target_id = _persist_target_vector(
        user_id,
        profile_name,
        goal_type,
        target_date,
        dimensions,
        target_values,
        milestones,
        description,
    )

    if not target_id:
        logger.error("Failed to persist target vector")
        return None

    # 6. Create and return TargetVector object
    return TargetVector(
        target_id=target_id,
        user_id=user_id,
        goal_type=goal_type,
        profile_name=profile_name,
        target_date=target_date,
        dimensions=dimensions,
        vector=target_values,
        milestones=milestones,
        created_at=datetime.now().isoformat(),
    )


def _apply_goal_adjustments(
    dimensions: List[str],
    baseline_values: List[float],
    goal_type: GoalType,
    custom_dimensions: Optional[Dict[str, float]] = None,
) -> List[float]:
    """
    Apply goal-specific adjustments to create a target vector.

    Different goals emphasize different metrics:
    - STRENGTH: Emphasizes strength dimensions
    - ENDURANCE: Emphasizes volume and consistency
    - WEIGHT_LOSS: Balanced with focus on volume
    - PERFORMANCE: Emphasizes intensity and consistency

    Args:
        dimensions: List of dimension names
        baseline_values: Current values for dimensions
        goal_type: Type of fitness goal
        custom_dimensions: Optional custom dimension values

    Returns:
        List of target values with goal-specific adjustments
    """
    # Start with a copy of the baseline
    target_values = baseline_values.copy()

    # Create dimension name to index mapping
    dim_to_idx = {dim: i for i, dim in enumerate(dimensions)}

    # Define improvement factors for different goal types
    # Values represent target improvements:
    # 0.0 = no change, 0.2 = 20% improvement, etc.
    improvement_map = {
        GoalType.STRENGTH: {
            "combined_strength": 0.3,  # 30% relative strength improvement
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

    # Get appropriate improvement factors
    improvements = improvement_map.get(goal_type, improvement_map[GoalType.DEFAULT])

    # Apply improvements to baseline values
    for dim, factor in improvements.items():
        if dim in dim_to_idx:
            idx = dim_to_idx[dim]
            # Improvement relative to current, capped at 1.0 (max normalized value)
            # Uses exponential diminishing returns for higher baseline values
            current_val = baseline_values[idx]
            room_for_improvement = 1.0 - current_val
            # Higher baseline values get smaller absolute improvements (diminishing returns)
            improvement = room_for_improvement * (1 - np.exp(-factor * 2))
            target_values[idx] = min(current_val + improvement, 1.0)

    # Apply custom dimension overrides if provided
    if custom_dimensions:
        for dim, value in custom_dimensions.items():
            if dim in dim_to_idx:
                idx = dim_to_idx[dim]
                # Ensure custom values are within valid range [0.0, 1.0]
                target_values[idx] = max(0.0, min(value, 1.0))

    # Ensure final_scalar is calculated appropriately
    if "final_scalar" in dim_to_idx:
        final_idx = dim_to_idx["final_scalar"]
        # Calculate as weighted average of other dimensions that improved
        improved_dims = [
            (dim, idx)
            for dim, idx in dim_to_idx.items()
            if dim in improvements and dim != "final_scalar"
        ]

        if improved_dims:
            # Get the average improvement of relevant dimensions
            improved_vals = [target_values[idx] for _, idx in improved_dims]
            current_vals = [baseline_values[idx] for _, idx in improved_dims]
            avg_improvement = sum(
                t - c for t, c in zip(improved_vals, current_vals)
            ) / len(improved_dims)

            # Apply to final scalar, but cap at 0.98 (1.0 is "perfect")
            target_values[final_idx] = min(
                baseline_values[final_idx] + avg_improvement,
                0.98,  # Cap at 0.98 (1.0 is "perfect")
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

    Args:
        dimensions: List of dimension names
        baseline_values: Starting vector values
        target_values: Final target vector values
        target_date: Date to reach final target

    Returns:
        List of milestone dictionaries with date and vector values
    """
    # Calculate total timeframe
    today = date.today()
    total_days = (target_date - today).days

    if total_days <= 0:
        logger.warning("Target date is today or in the past, no milestones created")
        return []

    milestones = []

    # Convert to numpy arrays for vectorized operations
    baseline_np = np.array(baseline_values)
    target_np = np.array(target_values)

    # Use non-linear progress curve for more realistic milestone progression
    # Early progress is faster, later progress slows down
    for percent_decimal in [0.25, 0.5, 0.75]:
        # Calculate milestone date (linear)
        milestone_days = int(total_days * percent_decimal)
        milestone_date = today + timedelta(days=milestone_days)

        # Calculate interpolated vector values (non-linear)
        # Use sigmoid-like curve: progress = percent^0.7 gives faster early progress
        progress_factor = percent_decimal**0.7
        milestone_np = baseline_np + (target_np - baseline_np) * progress_factor
        milestone_values = [round(float(v), 3) for v in milestone_np]

        milestones.append(
            {
                "percent": int(percent_decimal * 100),
                "date": milestone_date.isoformat(),
                "vector": milestone_values,
            }
        )

    return milestones


def _generate_goal_description(
    user_id: int,
    goal_type: GoalType,
    target_date: date,
    fitness_level: Optional[str] = None,
) -> str:
    """
    Generate a personalized goal description based on goal type and user profile.

    Args:
        user_id: User identifier
        goal_type: Type of fitness goal
        target_date: Date to reach target
        fitness_level: User's current fitness level

    Returns:
        Personalized goal description
    """
    # Get time frame
    days_to_target = (target_date - date.today()).days
    weeks = days_to_target // 7
    months = days_to_target // 30

    time_frame = (
        f"{months} months"
        if months > 1
        else f"{weeks} weeks" if weeks > 1 else f"{days_to_target} days"
    )

    # Get user name
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    user_name = row[0] if row else "User"

    # Use fitness level to tailor description
    level_prefix = ""
    if fitness_level:
        if fitness_level in ["Beginner", "Novice"]:
            level_prefix = "Foundational "
        elif fitness_level in ["Intermediate"]:
            level_prefix = "Intermediate "
        else:  # Advanced or Elite
            level_prefix = "Advanced "

    # Goal-specific descriptions
    if goal_type == GoalType.STRENGTH:
        return f"{level_prefix}Strength goal for {user_name}: Build significant strength gains over {time_frame} through progressive overload and compound movements."

    elif goal_type == GoalType.ENDURANCE:
        return f"{level_prefix}Endurance goal for {user_name}: Develop improved cardiovascular and muscular endurance over {time_frame} through consistent training volume."

    elif goal_type == GoalType.WEIGHT_LOSS:
        return f"{level_prefix}Body Composition goal for {user_name}: Transform body composition over {time_frame} through balanced training and increased energy expenditure."

    elif goal_type == GoalType.PERFORMANCE:
        return f"{level_prefix}Performance goal for {user_name}: Enhance overall athletic performance over {time_frame} through targeted training and capacity development."

    else:  # DEFAULT
        return f"{level_prefix}Fitness goal for {user_name}: Improve overall fitness over {time_frame} through balanced training approach."


def _persist_target_vector(
    user_id: int,
    profile_name: str,
    goal_type: GoalType,
    target_date: date,
    dimensions: List[str],
    vector: List[float],
    milestones: List[Dict[str, Any]],
    description: str = "",
) -> Optional[int]:
    """
    Persist the target vector and milestones to the database.

    Args:
        user_id: User identifier
        profile_name: Name of vector profile
        goal_type: Type of fitness goal
        target_date: Date to reach target
        dimensions: List of dimension names
        vector: Target vector values
        milestones: List of milestone vectors
        description: Goal description

    Returns:
        ID of created target vector record, or None if failed
    """
    try:
        # Convert lists to comma-separated strings
        dims_str = ",".join(dimensions)
        vec_str = ",".join(f"{v:.3f}" for v in vector)

        # Convert milestones to JSON-like string for storage
        milestone_str = "|".join(
            f"{m['percent']}:{m['date']}:{','.join(f'{v:.3f}' for v in m['vector'])}"
            for m in milestones
        )

        with create_conn() as conn:
            cur = conn.cursor()
            # Ensure table exists
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
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )

            # Insert target vector
            cur.execute(
                """
                INSERT INTO target_profile (
                    user_id, profile_name, goal_type, target_date, 
                    dimensions, vector, milestones, description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                    description,
                ),
            )
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        logger.error(f"Error persisting target vector: {str(e)}")
        return None


def get_target_vector(target_id: int) -> Optional[TargetVector]:
    """
    Retrieve a target vector by ID.

    Args:
        target_id: ID of target vector to retrieve

    Returns:
        TargetVector object if found, None otherwise
    """
    try:
        with create_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT user_id, profile_name, goal_type, target_date, 
                       dimensions, vector, milestones, created_at,
                       description, status, updated_at
                FROM target_profile
                WHERE target_id = ?
                """,
                (target_id,),
            )
            row = cur.fetchone()

        if not row:
            logger.warning(f"Target vector not found: target_id={target_id}")
            return None

        # Parse stored data
        (
            user_id,
            profile_name,
            goal_type_str,
            target_date_str,
            dims_str,
            vec_str,
            milestones_str,
            created_at,
            description,
            status,
            updated_at,
        ) = row

        # Convert to appropriate types
        dimensions = dims_str.split(",") if dims_str else []
        vector = [float(v) for v in vec_str.split(",")] if vec_str else []

        # Try to convert goal_type to enum
        try:
            goal_type = GoalType(goal_type_str)
        except ValueError:
            goal_type = goal_type_str

        # Convert target_date to date object
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = target_date_str

        # Parse milestones
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

        return TargetVector(
            target_id=target_id,
            user_id=user_id,
            profile_name=profile_name,
            goal_type=goal_type,
            target_date=target_date,
            dimensions=dimensions,
            vector=vector,
            milestones=milestones,
            created_at=created_at,
            description=description,
            status=status,
            updated_at=updated_at,
        )
    except Exception as e:
        logger.error(f"Error retrieving target vector: {str(e)}")
        return None


def get_user_targets(
    user_id: int, include_inactive: bool = False
) -> List[Dict[str, Any]]:
    """
    Retrieve all target vectors for a user.

    Args:
        user_id: User identifier
        include_inactive: Whether to include inactive/completed goals

    Returns:
        List of target vector summaries
    """
    try:
        with create_conn() as conn:
            cur = conn.cursor()

            query = """
                SELECT target_id, profile_name, goal_type, target_date, 
                       created_at, description, status, updated_at
                FROM target_profile
                WHERE user_id = ?
            """

            if not include_inactive:
                query += " AND status = 'active'"

            query += " ORDER BY CASE WHEN status = 'active' THEN 0 ELSE 1 END, created_at DESC"

            cur.execute(query, (user_id,))
            rows = cur.fetchall()

        targets = []
        today = date.today()

        for row in rows:
            (
                target_id,
                profile_name,
                goal_type,
                target_date_str,
                created_at,
                description,
                status,
                updated_at,
            ) = row

            # Calculate progress percentage
            try:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                start_date = datetime.strptime(created_at.split()[0], "%Y-%m-%d").date()

                total_days = (target_date - start_date).days
                days_passed = (today - start_date).days
                days_remaining = max(0, (target_date - today).days)

                if total_days <= 0:
                    time_progress_pct = 100.0
                else:
                    time_progress_pct = min(
                        100.0, max(0.0, days_passed / total_days * 100.0)
                    )

                # Calculate actual progress (approximation)
                try:
                    progress = calculate_goal_progress(user_id, target_id)
                    vector_progress_pct = progress.get("vector_progress_pct", 0)
                    on_track = progress.get("on_track", False)
                except Exception:
                    vector_progress_pct = 0
                    on_track = False
            except (ValueError, AttributeError):
                time_progress_pct = 0.0
                vector_progress_pct = 0.0
                days_remaining = 0
                on_track = False

            targets.append(
                {
                    "target_id": target_id,
                    "profile_name": profile_name,
                    "goal_type": goal_type,
                    "target_date": target_date_str,
                    "time_progress": round(time_progress_pct, 1),
                    "vector_progress": round(vector_progress_pct, 1),
                    "days_remaining": days_remaining,
                    "on_track": on_track,
                    "created_at": created_at,
                    "description": description,
                    "status": status,
                    "updated_at": updated_at,
                }
            )

        return targets
    except Exception as e:
        logger.error(f"Error getting user targets: {str(e)}")
        return []


def get_current_milestone(target_id: int) -> Optional[MilestoneVector]:
    """
    Get the current milestone for a target based on today's date.

    Returns the milestone closest to today without exceeding it.
    If today is past all milestones, returns the final target.

    Args:
        target_id: ID of target vector

    Returns:
        MilestoneVector object for current milestone
    """
    try:
        target = get_target_vector(target_id)
        if not target:
            logger.warning(f"Target vector not found: target_id={target_id}")
            return None

        today = date.today()

        # Convert target_date to date object if necessary
        if isinstance(target.target_date, str):
            try:
                target_date = datetime.strptime(target.target_date, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"Invalid target date format: {target.target_date}")
                return None
        else:
            target_date = target.target_date

        # If we're already at or past the target date, return the full target
        if today >= target_date:
            return MilestoneVector(
                dimensions=target.dimensions,
                vector=target.vector,
                percent=100,
                date=target_date,
                is_final=True,
            )

        # Check each milestone to find the current one
        current_milestone = None
        milestones = target.milestones if target.milestones else []

        # Sort milestones by percent for proper progression
        sorted_milestones = sorted(milestones, key=lambda m: m.get("percent", 0))

        for milestone in sorted_milestones:
            # Convert milestone date to date object
            try:
                milestone_date = datetime.strptime(milestone["date"], "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Invalid milestone date format: {milestone['date']}")
                continue

            if today >= milestone_date:
                # This milestone has been reached
                current_milestone = milestone
            else:
                # We've found the next milestone that hasn't been reached yet
                break

        # If we haven't reached first milestone yet, create a pro-rated initial milestone
        if current_milestone is None and sorted_milestones:
            # Get user vector for baseline
            user_vector = get_user_vector(target.user_id)
            if not user_vector:
                logger.warning(f"User vector not found: user_id={target.user_id}")
                return None

            # Get start date from target creation
            if isinstance(target.created_at, str):
                try:
                    start_date = datetime.strptime(
                        target.created_at.split()[0], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    start_date = today - timedelta(days=1)  # Fallback
            else:
                # Use yesterday as fallback
                start_date = today - timedelta(days=1)

            # Calculate time-based progress percentage
            total_days = (target_date - start_date).days
            days_passed = (today - start_date).days

            if total_days > 0:
                percent = (days_passed / total_days) * 100

                # Get first milestone for interpolation
                first_milestone = sorted_milestones[0]
                first_milestone_percent = first_milestone["percent"] / 100

                # Pro-rate vector between baseline and first milestone
                baseline_vector = user_vector.vector

                # Use numpy for vectorized operations
                baseline_np = np.array(baseline_vector)
                milestone_np = np.array(first_milestone["vector"])

                # Linear interpolation
                progress_ratio = min(1.0, percent / first_milestone["percent"])
                pro_rated_np = (
                    baseline_np + (milestone_np - baseline_np) * progress_ratio
                )
                pro_rated_vector = [round(float(v), 3) for v in pro_rated_np]

                return MilestoneVector(
                    dimensions=target.dimensions,
                    vector=pro_rated_vector,
                    percent=round(percent, 1),
                    date=today,
                    is_prorated=True,
                )

        # If we found a milestone, convert to MilestoneVector
        if current_milestone:
            return MilestoneVector(
                dimensions=target.dimensions,
                vector=current_milestone["vector"],
                percent=current_milestone["percent"],
                date=datetime.strptime(current_milestone["date"], "%Y-%m-%d").date(),
            )

        # If no milestone found and couldn't create pro-rated milestone, return initial state
        # Use user's current vector as the baseline
        user_vector = get_user_vector(target.user_id)
        if not user_vector:
            logger.warning(f"User vector not found: user_id={target.user_id}")
            return None

        return MilestoneVector(
            dimensions=user_vector.dimensions,
            vector=user_vector.vector,
            percent=0,
            date=today,
            is_initial=True,
        )
    except Exception as e:
        logger.error(f"Error getting current milestone: {str(e)}")
        return None


def calculate_goal_progress(user_id: int, target_id: int) -> Dict[str, Any]:
    """
    Calculate user's progress toward a specific target.

    Compares current vector to current milestone and final target.

    Args:
        user_id: User identifier
        target_id: ID of target vector

    Returns:
        Dictionary with detailed progress metrics
    """
    try:
        # Get target details
        target = get_target_vector(target_id)
        if not target:
            logger.error(f"Target not found: target_id={target_id}")
            raise ValueError(f"Target not found: target_id={target_id}")

        # Get current user vector
        current_vector = get_user_vector(user_id)
        if not current_vector:
            logger.error(f"User vector not found for user_id={user_id}")
            raise ValueError(f"User vector not found for user_id={user_id}")

        # Get current milestone
        current_milestone = get_current_milestone(target_id)

        # Calculate time-based progress
        today = date.today()

        # Convert dates to date objects if necessary
        if isinstance(target.created_at, str):
            try:
                start_date = datetime.strptime(
                    target.created_at.split()[0], "%Y-%m-%d"
                ).date()
            except ValueError:
                # Use 30 days ago as fallback
                start_date = today - timedelta(days=30)
        else:
            # Use 30 days ago as fallback
            start_date = today - timedelta(days=30)

        if isinstance(target.target_date, str):
            try:
                target_date = datetime.strptime(target.target_date, "%Y-%m-%d").date()
            except ValueError:
                # Use 60 days from now as fallback
                target_date = today + timedelta(days=60)
        else:
            target_date = target.target_date

        # Calculate timing metrics
        total_days = (target_date - start_date).days
        days_passed = (today - start_date).days
        days_remaining = max(0, (target_date - today).days)

        # Calculate time progress percentage
        time_progress_pct = (
            min(100.0, max(0.0, days_passed / total_days * 100.0))
            if total_days > 0
            else 100.0
        )

        # Calculate vector-based progress
        vector_progress = []
        overall_progress = 0.0
        progress_count = 0

        # Ensure we have dimension match
        common_dimensions = set(target.dimensions).intersection(
            set(current_vector.dimensions)
        )

        # Get original baseline vector
        original_user_vector = None
        with create_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT vector 
                FROM user_vector_history
                WHERE user_id = ? AND snapshot_date <= ?
                ORDER BY snapshot_date ASC
                LIMIT 1
                """,
                (user_id, start_date.isoformat()),
            )
            row = cur.fetchone()

        if row and row[0]:
            # Use historical baseline
            baseline_vector = [float(v) for v in row[0].split(",")]
        else:
            # No historical data, check if we can get the initial vector from the goal creation time
            with create_conn() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT vector 
                    FROM user_vector_history
                    WHERE user_id = ? AND snapshot_date <= ?
                    ORDER BY ABS(julianday(snapshot_date) - julianday(?))
                    LIMIT 1
                    """,
                    (
                        user_id,
                        (
                            target.created_at.split()[0]
                            if isinstance(target.created_at, str)
                            else target.created_at
                        ),
                        (
                            target.created_at.split()[0]
                            if isinstance(target.created_at, str)
                            else target.created_at
                        ),
                    ),
                )
                row = cur.fetchone()

            if row and row[0]:
                # Use closest historical vector to goal creation
                baseline_vector = [float(v) for v in row[0].split(",")]
            else:
                # No historical data at all, use current as fallback
                # This won't show progress accurately but prevents errors
                baseline_vector = current_vector.vector
                logger.warning(
                    f"No baseline vector found for progress calculation, using current vector"
                )

        # Create numpy arrays for vectorized operations
        current_np = np.array(current_vector.vector)
        target_np = np.array(target.vector)
        baseline_np = np.array(baseline_vector)

        # Get dimension weights based on goal type
        dimension_weights = _get_goal_dimension_weights(target.goal_type)

        # Calculate dimension importance for weighting
        importance_weights = {}
        for dim in common_dimensions:
            importance = dimension_weights.get(dim, 0.5)  # Default to medium importance
            importance_weights[dim] = importance

        # Compare for each dimension
        for dim in common_dimensions:
            try:
                # Get indices in respective vectors
                target_idx = target.dimensions.index(dim)
                current_idx = current_vector.dimensions.index(dim)
                baseline_idx = min(
                    current_idx, len(baseline_vector) - 1
                )  # Prevent index error

                # Get values
                target_val = target.vector[target_idx]
                current_val = current_vector.vector[current_idx]
                baseline_val = baseline_vector[baseline_idx]

                # Calculate progress percentage
                if abs(target_val - baseline_val) < 0.001:
                    # No change needed - either already at target or not a focus
                    progress_pct = 100.0 if current_val >= target_val else 0.0
                else:
                    # Calculate progress toward target
                    progress_pct = min(
                        100.0,
                        max(
                            0.0,
                            (current_val - baseline_val)
                            / (target_val - baseline_val)
                            * 100.0,
                        ),
                    )

                # Add to progress list
                vector_progress.append(
                    {
                        "dimension": dim,
                        "current": round(current_val, 3),
                        "target": round(target_val, 3),
                        "baseline": round(baseline_val, 3),
                        "progress_pct": round(progress_pct, 1),
                        "importance": importance_weights.get(dim, 0.5),
                    }
                )

                # Include dimensions in overall progress, weighted by importance
                importance = importance_weights.get(dim, 0.5)
                overall_progress += progress_pct * importance
                progress_count += importance

            except (ValueError, IndexError) as e:
                logger.warning(f"Error calculating progress for dimension {dim}: {e}")

        # Sort progress by importance then by dimension name
        vector_progress.sort(
            key=lambda x: (-x.get("importance", 0.5), x.get("dimension", ""))
        )

        # Calculate overall progress
        overall_progress_pct = (
            round(overall_progress / progress_count, 1) if progress_count > 0 else 0.0
        )

        # Advanced metrics: similarity scores
        current_similarity = weighted_similarity(
            current_np,
            target_np,
            weights=np.array(
                [importance_weights.get(dim, 0.5) for dim in target.dimensions]
            ),
        )
        baseline_similarity = weighted_similarity(
            baseline_np,
            target_np,
            weights=np.array(
                [importance_weights.get(dim, 0.5) for dim in target.dimensions]
            ),
        )

        # Calculate relative improvement in similarity
        if baseline_similarity < 0.99:  # Prevent division by near-zero
            similarity_improvement = (
                (current_similarity - baseline_similarity)
                / (1 - baseline_similarity)
                * 100
            )
        else:
            similarity_improvement = 0

        # Calculate expected progress at this point
        # Use sigmoid function to model expected progress curve
        # Early progress is faster, later progress slows down
        days_ratio = days_passed / total_days if total_days > 0 else 1.0
        expected_progress = 100 / (1 + np.exp(-10 * (days_ratio - 0.5)))

        # Compare to time-based expectation (on track if within 20% of expected)
        progress_ratio = (
            overall_progress_pct / expected_progress if expected_progress > 0 else 1.0
        )
        on_track = progress_ratio >= 0.8

        # Calculate progress status with more detail
        if progress_ratio >= 1.2:
            progress_status = "ahead"
        elif progress_ratio >= 0.8:
            progress_status = "on_track"
        elif progress_ratio >= 0.5:
            progress_status = "slightly_behind"
        else:
            progress_status = "behind"

        # Calculate projected completion
        # Based on current progress rate, when will goal be achieved?
        if days_passed > 0 and overall_progress_pct > 0:
            progress_rate = overall_progress_pct / days_passed  # % per day
            if progress_rate > 0:
                days_to_completion = (100 - overall_progress_pct) / progress_rate
                projected_completion = today + timedelta(days=int(days_to_completion))
            else:
                projected_completion = None
        else:
            projected_completion = None

        # Calculate next milestone
        next_milestone = None
        if current_milestone and target.milestones:
            # Find milestone after current one
            current_percent = current_milestone.percent
            for milestone in sorted(
                target.milestones, key=lambda m: m.get("percent", 0)
            ):
                if milestone["percent"] > current_percent:
                    next_milestone = {
                        "percent": milestone["percent"],
                        "date": milestone["date"],
                        "days_until": (
                            datetime.strptime(milestone["date"], "%Y-%m-%d").date()
                            - today
                        ).days,
                    }
                    break

        return {
            "target_id": target_id,
            "goal_type": (
                target.goal_type.value
                if isinstance(target.goal_type, GoalType)
                else target.goal_type
            ),
            "time_progress_pct": round(time_progress_pct, 1),
            "vector_progress_pct": overall_progress_pct,
            "status": progress_status,
            "on_track": on_track,
            "days_passed": days_passed,
            "days_remaining": days_remaining,
            "total_days": total_days,
            "current_milestone_pct": (
                current_milestone.percent if current_milestone else 0
            ),
            "dimension_progress": vector_progress,
            "target_date": (
                target_date.isoformat()
                if isinstance(target_date, date)
                else target_date
            ),
            "similarity": {
                "current": round(current_similarity * 100, 1),
                "baseline": round(baseline_similarity * 100, 1),
                "improvement": round(similarity_improvement, 1),
            },
            "expected_progress": round(expected_progress, 1),
            "projected_completion": (
                projected_completion.isoformat() if projected_completion else None
            ),
            "next_milestone": next_milestone,
        }
    except Exception as e:
        logger.error(f"Error calculating goal progress: {str(e)}")
        raise ValueError(f"Failed to calculate goal progress: {str(e)}")


def _get_goal_dimension_weights(goal_type: Union[GoalType, str]) -> Dict[str, float]:
    """
    Get dimension importance weights based on goal type.

    Args:
        goal_type: Type of fitness goal

    Returns:
        Dictionary mapping dimensions to importance weights (0-1)
    """
    # Convert string to enum if needed
    if isinstance(goal_type, str):
        try:
            goal_type = GoalType(goal_type)
        except ValueError:
            goal_type = GoalType.DEFAULT

    # Define dimension weights by goal type
    weights = {
        GoalType.STRENGTH: {
            "combined_strength": 1.0,
            "total_volume": 0.7,
            "intensity_avg": 0.8,
            "weekly_volume": 0.6,
            "training_days": 0.5,
            "consistency_pct": 0.4,
            "final_scalar": 0.7,
        },
        GoalType.ENDURANCE: {
            "combined_strength": 0.4,
            "total_volume": 0.7,
            "weekly_volume": 1.0,
            "training_days": 0.9,
            "consistency_pct": 0.8,
            "intensity_avg": 0.5,
            "final_scalar": 0.7,
        },
        GoalType.WEIGHT_LOSS: {
            "combined_strength": 0.3,
            "total_volume": 0.7,
            "weekly_volume": 1.0,
            "training_days": 0.9,
            "consistency_pct": 0.6,
            "intensity_avg": 0.4,
            "final_scalar": 0.7,
        },
        GoalType.PERFORMANCE: {
            "combined_strength": 0.8,
            "total_volume": 0.7,
            "intensity_avg": 0.9,
            "weekly_volume": 0.8,
            "training_days": 0.7,
            "consistency_pct": 1.0,
            "final_scalar": 0.8,
        },
        GoalType.DEFAULT: {
            "combined_strength": 0.7,
            "total_volume": 0.7,
            "weekly_volume": 0.7,
            "training_days": 0.7,
            "consistency_pct": 0.7,
            "intensity_avg": 0.7,
            "final_scalar": 0.7,
        },
    }

    return weights.get(goal_type, weights[GoalType.DEFAULT])


def update_target_vector(
    target_id: int,
    custom_dimensions: Optional[Dict[str, float]] = None,
    extend_target_date: Optional[int] = None,
    new_description: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[TargetVector]:
    """
    Update an existing target vector with custom values or extended date.

    Args:
        target_id: ID of target vector to update
        custom_dimensions: Custom dimension values to apply
        extend_target_date: Number of days to extend target date
        new_description: Updated goal description
        status: New goal status (active, completed, abandoned)

    Returns:
        Updated TargetVector if successful, None otherwise
    """
    try:
        # Get current target
        target = get_target_vector(target_id)
        if not target:
            logger.error(f"Target not found: target_id={target_id}")
            return None

        # Update target date if requested
        new_target_date = None
        if extend_target_date:
            # Convert target_date to date object if necessary
            if isinstance(target.target_date, str):
                try:
                    current_date = datetime.strptime(
                        target.target_date, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    logger.error(f"Invalid target date format: {target.target_date}")
                    return None
            else:
                current_date = target.target_date

            # Calculate new date
            new_target_date = current_date + timedelta(days=extend_target_date)

        # Update dimension values if custom values provided
        new_vector = target.vector.copy()
        if custom_dimensions:
            dim_to_idx = {dim: i for i, dim in enumerate(target.dimensions)}

            for dim, value in custom_dimensions.items():
                if dim in dim_to_idx:
                    idx = dim_to_idx[dim]
                    # Ensure custom values are within valid range [0.0, 1.0]
                    new_vector[idx] = max(0.0, min(value, 1.0))

        # Only proceed if we have changes
        if (
            not custom_dimensions
            and not new_target_date
            and not new_description
            and not status
        ):
            logger.warning("No changes requested for target update")
            return target

        # Recalculate milestones if date or vector values changed
        new_milestones = target.milestones
        if new_target_date or custom_dimensions:
            # Get user vector for baseline
            user_vector = get_user_vector(target.user_id)
            if user_vector:
                new_milestones = _calculate_milestone_vectors(
                    target.dimensions,
                    user_vector.vector,
                    new_vector,
                    new_target_date
                    or (
                        datetime.strptime(target.target_date, "%Y-%m-%d").date()
                        if isinstance(target.target_date, str)
                        else target.target_date
                    ),
                )

        # Update in database
        with create_conn() as conn:
            cur = conn.cursor()

            # Prepare update SQL and parameters
            sql_parts = []
            params = []

            if new_target_date:
                sql_parts.append("target_date = ?")
                params.append(new_target_date.isoformat())

            if custom_dimensions:
                sql_parts.append("vector = ?")
                vec_str = ",".join(f"{v:.3f}" for v in new_vector)
                params.append(vec_str)

            if new_milestones != target.milestones:
                sql_parts.append("milestones = ?")
                milestone_str = "|".join(
                    f"{m['percent']}:{m['date']}:{','.join(f'{v:.3f}' for v in m['vector'])}"
                    for m in new_milestones
                )
                params.append(milestone_str)

            if new_description:
                sql_parts.append("description = ?")
                params.append(new_description)

            if status:
                sql_parts.append("status = ?")
                params.append(status)

            sql_parts.append("updated_at = CURRENT_TIMESTAMP")

            # Build and execute SQL
            if sql_parts:
                sql = f"UPDATE target_profile SET {', '.join(sql_parts)} WHERE target_id = ?"
                params.append(target_id)
                cur.execute(sql, params)
                conn.commit()

        # Return updated target
        return get_target_vector(target_id)
    except Exception as e:
        logger.error(f"Error updating target vector: {str(e)}")
        return None


def generate_goal_recommendations(
    user_id: int,
    focus_area: Optional[str] = None,
    fitness_level: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Generate personalized goal recommendations based on user's profile.

    Args:
        user_id: User identifier
        focus_area: Optional area to focus recommendations on
        fitness_level: Optional fitness level override
        limit: Maximum number of recommendations to return

    Returns:
        List of goal recommendations with details
    """
    try:
        # Get user vector
        user_vector = get_user_vector(user_id)
        if not user_vector:
            logger.error(f"User vector not found for user_id={user_id}")
            return []

        # Convert to dict for easier access
        user_metrics = {
            dim: val for dim, val in zip(user_vector.dimensions, user_vector.vector)
        }

        # Get user's activity level and fitness tier
        activity_level = fitness_level or user_vector.activity_level or "Beginner"

        # Check which metrics are lowest
        key_metrics = [
            ("combined_strength", "strength"),
            ("weekly_volume", "volume"),
            ("training_days", "frequency"),
            ("intensity_avg", "intensity"),
            ("consistency_pct", "consistency"),
        ]

        # Sort metrics from lowest to highest
        sorted_metrics = sorted(
            [
                (dim, label, user_metrics.get(dim, 0.0))
                for dim, label in key_metrics
                if dim in user_metrics
            ],
            key=lambda x: x[2],
        )

        # Focus on the lowest few metrics
        focus_metrics = sorted_metrics[:3]

        # Generate recommendations based on weak areas
        recommendations = []
        for dim, label, value in focus_metrics:
            if value < 0.3:  # Very low
                severity = "critical"
            elif value < 0.5:  # Low
                severity = "significant"
            elif value < 0.7:  # Moderate
                severity = "moderate"
            else:
                severity = "minor"

            # Skip if not in focus area
            if focus_area and focus_area.lower() != label.lower():
                continue

            # Generate specific recommendation based on metric
            if label == "strength":
                if activity_level in ("Beginner", "Novice"):
                    rec = {
                        "goal_type": GoalType.STRENGTH.value,
                        "title": "Build Foundational Strength",
                        "description": "Focus on compound movements to develop base strength",
                        "target_improvement": 30,
                        "recommended_duration": 90,  # days
                        "priority": 5 - sorted_metrics.index((dim, label, value)),
                        "severity": severity,
                        "focus_dimension": dim,
                        "custom_targets": {
                            dim: min(value + 0.3, 0.9),
                            "intensity_avg": min(
                                user_metrics.get("intensity_avg", 0.3) + 0.2, 0.9
                            ),
                        },
                    }
                else:
                    rec = {
                        "goal_type": GoalType.STRENGTH.value,
                        "title": "Advanced Strength Development",
                        "description": "Progressive overload with periodized strength training",
                        "target_improvement": 20,
                        "recommended_duration": 120,  # days
                        "priority": 5 - sorted_metrics.index((dim, label, value)),
                        "severity": severity,
                        "focus_dimension": dim,
                        "custom_targets": {
                            dim: min(value + 0.2, 0.95),
                            "intensity_avg": min(
                                user_metrics.get("intensity_avg", 0.5) + 0.15, 0.95
                            ),
                        },
                    }

            elif label == "volume":
                rec = {
                    "goal_type": GoalType.ENDURANCE.value,
                    "title": "Build Work Capacity",
                    "description": "Gradually increase training volume for improved adaptation",
                    "target_improvement": 40,
                    "recommended_duration": 60,  # days
                    "priority": 5 - sorted_metrics.index((dim, label, value)),
                    "severity": severity,
                    "focus_dimension": dim,
                    "custom_targets": {
                        dim: min(value + 0.4, 0.9),
                        "training_days": min(
                            user_metrics.get("training_days", 0.3) + 0.3, 0.9
                        ),
                    },
                }

            elif label == "frequency":
                rec = {
                    "goal_type": GoalType.DEFAULT.value,
                    "title": "Establish Regular Training Habit",
                    "description": "Create consistent weekly training schedule",
                    "target_improvement": 50,
                    "recommended_duration": 30,  # days
                    "priority": 5 - sorted_metrics.index((dim, label, value)),
                    "severity": severity,
                    "focus_dimension": dim,
                    "custom_targets": {
                        dim: min(value + 0.5, 0.9),
                        "consistency_pct": min(
                            user_metrics.get("consistency_pct", 0.3) + 0.3, 0.9
                        ),
                    },
                }

            elif label == "intensity":
                rec = {
                    "goal_type": GoalType.PERFORMANCE.value,
                    "title": "Intensity Optimization",
                    "description": "Focus on quality over quantity with higher intensity sessions",
                    "target_improvement": 30,
                    "recommended_duration": 45,  # days
                    "priority": 5 - sorted_metrics.index((dim, label, value)),
                    "severity": severity,
                    "focus_dimension": dim,
                    "custom_targets": {
                        dim: min(value + 0.3, 0.9),
                        "combined_strength": min(
                            user_metrics.get("combined_strength", 0.3) + 0.2, 0.9
                        ),
                    },
                }

            elif label == "consistency":
                rec = {
                    "goal_type": GoalType.PERFORMANCE.value,
                    "title": "Training Consistency",
                    "description": "Develop consistent training patterns for optimal adaptation",
                    "target_improvement": 40,
                    "recommended_duration": 60,  # days
                    "priority": 5 - sorted_metrics.index((dim, label, value)),
                    "severity": severity,
                    "focus_dimension": dim,
                    "custom_targets": {
                        dim: min(value + 0.4, 0.9),
                        "training_days": min(
                            user_metrics.get("training_days", 0.3) + 0.2, 0.9
                        ),
                    },
                }

            recommendations.append(rec)

        # Add body composition recommendation if user has Weight-Loss goal type in preferences
        with create_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT goal FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()

        if row and row[0] == "Weight-Loss":
            recommendations.append(
                {
                    "goal_type": GoalType.WEIGHT_LOSS.value,
                    "title": "Body Composition Improvement",
                    "description": "Balanced approach to training for body composition changes",
                    "target_improvement": 30,
                    "recommended_duration": 90,  # days
                    "priority": 3,
                    "severity": "moderate",
                    "focus_dimension": "weekly_volume",
                    "custom_targets": {
                        "weekly_volume": min(
                            user_metrics.get("weekly_volume", 0.3) + 0.4, 0.9
                        ),
                        "training_days": min(
                            user_metrics.get("training_days", 0.3) + 0.4, 0.9
                        ),
                    },
                }
            )

        # Sort by priority and return limited number
        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: (x["priority"], -len(x.get("custom_targets", {}))),
            reverse=True,
        )
        return sorted_recommendations[:limit]
    except Exception as e:
        logger.error(f"Error generating goal recommendations: {str(e)}")
        return []


def create_goal_from_recommendation(
    user_id: int, recommendation_id: int, custom_duration: Optional[int] = None
) -> Optional[TargetVector]:
    """
    Create a new goal based on a specific recommendation.

    Args:
        user_id: User identifier
        recommendation_id: ID of recommendation to convert to goal
        custom_duration: Optional custom duration in days

    Returns:
        Created TargetVector if successful, None otherwise
    """
    try:
        # Get user's recommendations
        recommendations = generate_goal_recommendations(user_id, limit=10)

        # Find the specific recommendation
        recommendation = None
        for rec in recommendations:
            if rec.get("id", id(rec)) == recommendation_id:
                recommendation = rec
                break

        if not recommendation:
            logger.error(f"Recommendation not found: id={recommendation_id}")
            return None

        # Calculate target date
        duration = custom_duration or recommendation.get("recommended_duration", 90)
        target_date = date.today() + timedelta(days=duration)

        # Extract goal type and custom targets
        goal_type = recommendation.get("goal_type", GoalType.DEFAULT.value)
        custom_targets = recommendation.get("custom_targets", {})
        description = recommendation.get("description", "")

        # Create the goal
        return initialize_target_vector(
            user_id=user_id,
            goal_type=goal_type,
            target_date=target_date,
            custom_dimensions=custom_targets,
            description=description,
        )
    except Exception as e:
        logger.error(f"Error creating goal from recommendation: {str(e)}")
        return None


def get_goal_similarity(target_id: int, compare_id: int) -> Dict[str, Any]:
    """
    Calculate similarity between two goals.

    Args:
        target_id: ID of first target vector
        compare_id: ID of second target vector

    Returns:
        Dictionary with similarity metrics
    """
    try:
        # Get both target vectors
        target1 = get_target_vector(target_id)
        target2 = get_target_vector(compare_id)

        if not target1 or not target2:
            logger.error(
                f"One or both target vectors not found: {target_id}, {compare_id}"
            )
            return {
                "similarity": 0,
                "common_dimensions": 0,
                "dimension_similarities": {},
            }

        # Find common dimensions
        common_dims = set(target1.dimensions).intersection(set(target2.dimensions))

        if not common_dims:
            logger.warning(
                f"No common dimensions between targets: {target_id}, {compare_id}"
            )
            return {
                "similarity": 0,
                "common_dimensions": 0,
                "dimension_similarities": {},
            }

        # Create numpy arrays with only common dimensions
        dims1 = []
        dims2 = []

        for dim in common_dims:
            idx1 = target1.dimensions.index(dim)
            idx2 = target2.dimensions.index(dim)
            dims1.append(target1.vector[idx1])
            dims2.append(target2.vector[idx2])

        np1 = np.array(dims1)
        np2 = np.array(dims2)

        # Calculate overall similarity
        similarity = weighted_similarity(np1, np2)

        # Calculate per-dimension similarities
        dimension_similarities = {}
        for dim in common_dims:
            idx1 = target1.dimensions.index(dim)
            idx2 = target2.dimensions.index(dim)
            val1 = target1.vector[idx1]
            val2 = target2.vector[idx2]

            # Similarity formula for single values
            dim_similarity = 1.0 - abs(val1 - val2)
            dimension_similarities[dim] = round(dim_similarity, 2)

        return {
            "similarity": round(similarity, 2),
            "common_dimensions": len(common_dims),
            "dimension_similarities": dimension_similarities,
            "target1_goal_type": (
                target1.goal_type.value
                if isinstance(target1.goal_type, GoalType)
                else target1.goal_type
            ),
            "target2_goal_type": (
                target2.goal_type.value
                if isinstance(target2.goal_type, GoalType)
                else target2.goal_type
            ),
        }
    except Exception as e:
        logger.error(f"Error calculating goal similarity: {str(e)}")
        return {"similarity": 0, "error": str(e)}


def archive_completed_goals(user_id: int) -> int:
    """
    Automatically mark goals as completed if they are past their target date
    and have high progress.

    Args:
        user_id: User identifier

    Returns:
        Number of goals archived
    """
    try:
        # Get all active goals
        with create_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT target_id
                FROM target_profile
                WHERE user_id = ? AND status = 'active' AND target_date < ?
                """,
                (user_id, date.today().isoformat()),
            )
            expired_goals = [row[0] for row in cur.fetchall()]

        # Check progress on each expired goal
        completed_count = 0
        for goal_id in expired_goals:
            try:
                progress = calculate_goal_progress(user_id, goal_id)
                vector_progress = progress.get("vector_progress_pct", 0)

                # Mark as completed if progress is high
                if vector_progress >= 80:
                    update_target_vector(goal_id, status="completed")
                    completed_count += 1
                # Otherwise mark as expired
                else:
                    update_target_vector(goal_id, status="expired")
            except Exception as e:
                logger.warning(f"Error processing expired goal {goal_id}: {str(e)}")

        return completed_count
    except Exception as e:
        logger.error(f"Error archiving completed goals: {str(e)}")
        return 0
