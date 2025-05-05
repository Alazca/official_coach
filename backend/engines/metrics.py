import logging

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from statistics import mean, pstdev

from backend.database.db import create_conn
from backend.models.models import ActivityLevel

logger = logging.getLogger(__name__)


def get_combined_lift_strength_metric(
    user_id: int, lifts: Optional[List[str]] = None
) -> float:
    """
    Compute an average relative strength metric across major lifts.

    This calculates the average ratio of 1RM weight to bodyweight
    across the specified lifts (or default major compound lifts).

    Args:
        user_id: User identifier
        lifts: Optional list of specific lifts to include

    Returns:
        Average relative strength ratio (0.0 if no data)
    """
    # Determine which lifts to include
    if lifts is None:
        with create_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT name
                FROM exercises
                WHERE category IN ('Compound', 'Olympic-Style')
                """
            )
            lifts = [row[0] for row in cur.fetchall()]

    if not lifts:
        logger.warning(
            f"No lifts found for strength metric calculation for user {user_id}"
        )
        return 0.0

    # Get user bodyweight
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT weight FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()

    bodyweight = float(row[0] or 0.0) if row else 0.0
    if bodyweight <= 0:
        logger.warning(f"Invalid bodyweight for user {user_id}")
        return 0.0

    # Compute ratios for each lift
    ratios: List[float] = []
    with create_conn() as conn:
        cur = conn.cursor()
        for lift in lifts:
            cur.execute(
                """
                SELECT MAX(ws.lifting_weight)
                FROM workout_sets ws
                JOIN workouts w ON ws.workout_id = w.workout_id
                JOIN exercises e ON ws.exercise_id = e.exercise_id
                WHERE w.user_id = ?
                  AND ws.is_one_rm = 1
                  AND e.name = ?
                """,
                (user_id, lift),
            )
            rm_row = cur.fetchone()
            rm = float(rm_row[0] or 0.0) if rm_row else 0.0
            if rm > 0:
                ratios.append(rm / bodyweight)

    if not ratios:
        logger.info(f"No valid lift data found for user {user_id}")
        return 0.0

    # Return average relative strength
    return round(sum(ratios) / len(ratios), 3)


def get_strength_metrics(user_id: int, days: int = 7) -> Dict[str, float]:
    """
    Calculate raw strength metrics over specified time period.

    Args:
        user_id: User identifier
        days: Lookback period in days

    Returns:
        Dictionary of strength metrics:
        - combined_strength: relative lift/bodyweight metric
        - total_volume: sum of sets*reps*weight over period
        - volume_percentile: percentile rank compared to all users
    """
    today = date.today()
    start_date = (today - timedelta(days=days)).isoformat()
    end_date = today.isoformat()

    # Calculate combined relative strength
    combined_strength = get_combined_lift_strength_metric(user_id)

    # Calculate total training volume
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT SUM(ws.sets * ws.reps * ws.lifting_weight) AS total_volume
            FROM workout_sets ws
            JOIN workouts w ON ws.workout_id = w.workout_id
            WHERE w.user_id = ?
              AND w.workout_date BETWEEN ? AND ?
            """,
            (user_id, start_date, end_date),
        )
        row = cur.fetchone()
    total_volume = float(row[0] or 0.0) if row else 0.0

    # Calculate volume percentile among all users
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT w.user_id, SUM(ws.sets * ws.reps * ws.lifting_weight) AS vol
            FROM workout_sets ws
            JOIN workouts w ON ws.workout_id = w.workout_id
            WHERE w.workout_date BETWEEN ? AND ?
            GROUP BY w.user_id
            """,
            (start_date, end_date),
        )
        rows = cur.fetchall()

    volumes = sorted([float(r[1] or 0.0) for r in rows])
    if volumes and total_volume > 0:
        # Find index where our volume would be inserted
        import bisect

        idx = bisect.bisect_left(volumes, total_volume)
        volume_percentile = (idx / len(volumes)) * 100.0
    else:
        volume_percentile = 0.0

    return {
        "combined_strength": round(combined_strength, 3),
        "total_volume": round(total_volume, 2),
        "volume_percentile": round(volume_percentile, 1),
    }


def get_conditioning_metrics(user_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Calculate raw conditioning metrics over specified time period.

    Args:
        user_id: User identifier
        days: Lookback period in days

    Returns:
        Dictionary of conditioning metrics:
        - weekly_volume: total workout volume over period
        - training_days: number of distinct workout days
        - volume_change_pct: percent change vs prior period
        - intensity_avg: volume per rep
        - consistency_pct: standard deviation as percent of mean
    """
    today = date.today()
    start_current = today - timedelta(days=days)
    prev_start = start_current - timedelta(days=days)

    # Get daily volumes for current period
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT w.workout_date,
                   SUM(ws.sets * ws.reps * ws.lifting_weight) AS day_vol,
                   SUM(ws.sets * ws.reps) AS day_reps
            FROM workout_sets ws
            JOIN workouts w ON ws.workout_id = w.workout_id
            WHERE w.user_id = ?
              AND w.workout_date BETWEEN ? AND ?
            GROUP BY w.workout_date
            """,
            (user_id, start_current.isoformat(), today.isoformat()),
        )
        days_data = cur.fetchall()

    # Extract metrics from daily data
    daily_vols = [float(d[1] or 0.0) for d in days_data if d[1] is not None]
    total_reps = (
        sum(float(d[2] or 0) for d in days_data if d[2] is not None) or 1
    )  # Avoid div by zero

    weekly_volume = sum(daily_vols)
    training_days = len(daily_vols)

    # Calculate intensity (volume per rep)
    intensity_avg = weekly_volume / total_reps if total_reps > 0 else 0.0

    # Calculate consistency (inverse of coefficient of variation)
    if daily_vols and len(daily_vols) > 1:
        try:
            consistency_pct = (pstdev(daily_vols) / mean(daily_vols)) * 100.0
        except (ZeroDivisionError, ValueError):
            consistency_pct = 0.0
    else:
        consistency_pct = 0.0

    # Get previous period volume
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT SUM(ws.sets * ws.reps * ws.lifting_weight)
            FROM workout_sets ws
            JOIN workouts w ON ws.workout_id = w.workout_id
            WHERE w.user_id = ?
              AND w.workout_date BETWEEN ? AND ?
            """,
            (user_id, prev_start.isoformat(), start_current.isoformat()),
        )
        prev_vol_row = cur.fetchone()

    # Calculate volume change percentage
    prev_vol = float(prev_vol_row[0] or 0.0) if prev_vol_row else 0.0

    if prev_vol > 0:
        volume_change_pct = ((weekly_volume - prev_vol) / prev_vol) * 100.0
    else:
        # If no previous volume, consider it a 100% increase if we have volume now
        volume_change_pct = 100.0 if weekly_volume > 0 else 0.0

    return {
        "weekly_volume": round(weekly_volume, 2),
        "training_days": training_days,
        "volume_change_pct": round(volume_change_pct, 1),
        "intensity_avg": round(intensity_avg, 2),
        "consistency_pct": round(consistency_pct, 1),
    }


def get_readiness_metrics(user_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Calculate readiness metrics from daily check-ins.

    Args:
        user_id: User identifier
        days: Lookback period in days

    Returns:
        Dictionary of readiness metrics:
        - avg_readiness: Average readiness score
        - trend: Direction and magnitude of trend
        - sleep_quality: Average sleep score
        - recovery_score: Computed recovery metric
    """
    today = date.today()
    start_date = (today - timedelta(days=days)).isoformat()

    # Get readiness scores for period
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT readiness_level, readiness_date, 
                   alignment_score, overtraining_score
            FROM readiness_scores
            WHERE user_id = ?
              AND readiness_date BETWEEN ? AND ?
            ORDER BY readiness_date
            """,
            (user_id, start_date, today.isoformat()),
        )
        readiness_data = cur.fetchall()

    # Get daily check-ins for period
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT sleep_quality, stress_level, energy_level, 
                   soreness_level, check_in_date
            FROM daily_checkins
            WHERE user_id = ?
              AND check_in_date BETWEEN ? AND ?
            ORDER BY check_in_date
            """,
            (user_id, start_date, today.isoformat()),
        )
        checkin_data = cur.fetchall()

    # Process readiness scores
    if readiness_data:
        readiness_scores = [
            float(r[0] or 0) for r in readiness_data if r[0] is not None
        ]
        readiness_dates = [r[1] for r in readiness_data if r[1] is not None]
        avg_readiness = (
            sum(readiness_scores) / len(readiness_scores) if readiness_scores else 0
        )

        # Calculate trend (difference between first and last half)
        if len(readiness_scores) >= 4:
            mid_point = len(readiness_scores) // 2
            first_half = readiness_scores[:mid_point]
            second_half = readiness_scores[mid_point:]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            trend_pct = (
                ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
            )
            trend_direction = (
                "improving"
                if trend_pct > 5
                else "declining" if trend_pct < -5 else "stable"
            )
        else:
            trend_pct = 0
            trend_direction = "stable"
    else:
        avg_readiness = 0
        trend_pct = 0
        trend_direction = "unknown"

    # Process check-in data
    if checkin_data:
        sleep_scores = [float(c[0] or 0) for c in checkin_data if c[0] is not None]
        stress_scores = [float(c[1] or 0) for c in checkin_data if c[1] is not None]
        energy_scores = [float(c[2] or 0) for c in checkin_data if c[2] is not None]
        soreness_scores = [float(c[3] or 0) for c in checkin_data if c[3] is not None]

        avg_sleep = sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0
        avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0
        avg_energy = sum(energy_scores) / len(energy_scores) if energy_scores else 0
        avg_soreness = (
            sum(soreness_scores) / len(soreness_scores) if soreness_scores else 0
        )

        # Calculate recovery score (sleep + energy - stress - soreness)
        # Normalize to 0-100 scale
        recovery_score = ((avg_sleep + avg_energy) / 20) * 50 + (
            (20 - avg_stress - avg_soreness) / 20
        ) * 50
    else:
        avg_sleep = 0
        recovery_score = 0

    return {
        "avg_readiness": round(avg_readiness, 1),
        "trend": {"direction": trend_direction, "percent": round(trend_pct, 1)},
        "sleep_quality": round(avg_sleep, 1),
        "recovery_score": round(recovery_score, 1),
    }


def get_workout_distribution(user_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Calculate workout type distribution and frequency.

    Args:
        user_id: User identifier
        days: Lookback period in days

    Returns:
        Dictionary with workout distribution data:
        - workout_types: Percentage breakdown by type
        - frequency: Average workouts per week
        - duration: Average workout duration in minutes
        - preferred_time: Most common workout time of day
    """
    today = date.today()
    start_date = (today - timedelta(days=days)).isoformat()

    # Get workout data
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT workout_type, workout_date, 
                   strftime('%H', created_at) as hour,
                   julianday(max(created_at)) - julianday(min(created_at)) as duration
            FROM workouts
            WHERE user_id = ?
              AND workout_date BETWEEN ? AND ?
            GROUP BY workout_id
            """,
            (user_id, start_date, today.isoformat()),
        )
        workout_data = cur.fetchall()

    if not workout_data:
        return {
            "workout_types": {},
            "frequency": 0,
            "duration": 0,
            "preferred_time": "unknown",
        }

    # Calculate type distribution
    type_counts = {}
    hours = []
    durations = []

    for row in workout_data:
        workout_type = row[0]
        hour = int(row[2]) if row[2] else None
        duration = float(row[3] * 24 * 60) if row[3] else None  # Convert to minutes

        if workout_type:
            type_counts[workout_type] = type_counts.get(workout_type, 0) + 1
        if hour is not None:
            hours.append(hour)
        if duration is not None:
            durations.append(duration)

    total_workouts = len(workout_data)
    type_percentages = {k: (v / total_workouts) * 100 for k, v in type_counts.items()}

    # Calculate frequency (workouts per week)
    weeks = days / 7
    frequency = total_workouts / weeks if weeks > 0 else 0

    # Calculate average duration
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Determine preferred time
    if hours:
        from collections import Counter

        hour_counter = Counter(hours)
        preferred_hour = hour_counter.most_common(1)[0][0]

        # Map to time of day
        if 5 <= preferred_hour < 12:
            preferred_time = "morning"
        elif 12 <= preferred_hour < 17:
            preferred_time = "afternoon"
        elif 17 <= preferred_hour < 21:
            preferred_time = "evening"
        else:
            preferred_time = "night"
    else:
        preferred_time = "unknown"

    return {
        "workout_types": {k: round(v, 1) for k, v in type_percentages.items()},
        "frequency": round(frequency, 1),
        "duration": round(avg_duration, 0),
        "preferred_time": preferred_time,
    }


def get_performance_trend(
    user_id: int, exercise_name: str, days: int = 90
) -> Dict[str, Any]:
    """
    Calculate performance trend for a specific exercise.

    Args:
        user_id: User identifier
        exercise_name: Name of exercise to analyze
        days: Lookback period in days

    Returns:
        Dictionary with performance trend data:
        - data_points: List of (date, weight, reps) tuples
        - estimated_1rm: Current estimated 1RM
        - max_weight: Maximum weight lifted
        - progression: Percentage improvement over period
    """
    today = date.today()
    start_date = (today - timedelta(days=days)).isoformat()

    # Get exercise ID
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT exercise_id FROM exercises WHERE name = ?", (exercise_name,)
        )
        exercise_row = cur.fetchone()

    if not exercise_row:
        return {
            "data_points": [],
            "estimated_1rm": 0,
            "max_weight": 0,
            "progression": 0,
        }

    exercise_id = exercise_row[0]

    # Get performance data
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT w.workout_date, ws.lifting_weight, ws.reps, ws.is_one_rm
            FROM workout_sets ws
            JOIN workouts w ON ws.workout_id = w.workout_id
            WHERE w.user_id = ?
              AND ws.exercise_id = ?
              AND w.workout_date BETWEEN ? AND ?
            ORDER BY w.workout_date
            """,
            (user_id, exercise_id, start_date, today.isoformat()),
        )
        performance_data = cur.fetchall()

    if not performance_data:
        return {
            "data_points": [],
            "estimated_1rm": 0,
            "max_weight": 0,
            "progression": 0,
        }

    # Process performance data
    data_points = []
    actual_1rms = []

    for row in performance_data:
        workout_date = row[0]
        weight = float(row[1]) if row[1] else 0
        reps = int(row[2]) if row[2] else 0
        is_1rm = bool(row[3]) if row[3] is not None else False

        if weight > 0 and reps > 0:
            # Brzycki formula for estimated 1RM
            # 1RM = Weight × (36 / (37 - Reps))
            estimated_1rm = weight * (36 / (37 - min(reps, 36)))
            data_points.append((workout_date, weight, reps, estimated_1rm))

        if is_1rm and weight > 0:
            actual_1rms.append((workout_date, weight))

    # Calculate metrics
    if data_points:
        # Sort by date
        data_points.sort(key=lambda x: x[0])

        # Get current estimated 1RM (from latest workout)
        current_1rm = data_points[-1][3]

        # Find max weight
        max_weight = max(point[1] for point in data_points)

        # Calculate progression
        if len(data_points) >= 2:
            first_date = data_points[0][0]
            first_1rm = data_points[0][3]

            last_date = data_points[-1][0]
            last_1rm = data_points[-1][3]

            # Only calculate progression if we have at least a week of data
            date_diff = datetime.strptime(last_date, "%Y-%m-%d") - datetime.strptime(
                first_date, "%Y-%m-%d"
            )
            if date_diff.days >= 7 and first_1rm > 0:
                progression = ((last_1rm - first_1rm) / first_1rm) * 100
            else:
                progression = 0
        else:
            progression = 0
    else:
        current_1rm = 0
        max_weight = 0
        progression = 0

    # Use actual 1RM if available, otherwise use estimated
    if actual_1rms:
        actual_1rms.sort(key=lambda x: x[0])  # Sort by date
        latest_actual_1rm = actual_1rms[-1][1]
        final_1rm = max(latest_actual_1rm, current_1rm)
    else:
        final_1rm = current_1rm

    return {
        "data_points": [(d[0], d[1], d[2]) for d in data_points],
        "estimated_1rm": round(final_1rm, 1),
        "max_weight": round(max_weight, 1),
        "progression": round(progression, 1),
    }
