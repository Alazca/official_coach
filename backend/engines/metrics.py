from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from statistics import mean, pstdev

from backend.database.db import create_conn


def get_combined_lift_strength_metric(
    user_id: int, lifts: Optional[List[str]] = None
) -> float:
    """
    Compute an average relative strength metric across major lifts:
      - If no lifts provided, fetch default major lifts (Compound & Olympic-Style) from the DB
      - Fetch user's bodyweight
      - For each lift, fetch latest 1RM
      - Compute lift 1RM / bodyweight
      - Return average ratio (0.0 if no data)
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
        return 0.0

    # Get user bodyweight
    with create_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT weight FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    bodyweight = float(row[0] or 0.0) if row else 0.0
    if bodyweight <= 0:
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
                  JOIN workouts w   ON ws.workout_id = w.workout_id
                  JOIN exercises e  ON ws.exercise_id = e.exercise_id
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
        return 0.0

    # Return average relative strength
    return round(sum(ratios) / len(ratios), 3)


def get_strength_metrics(user_id: int, days: int = 7) -> Dict[str, float]:
    """
    Raw strength metrics:
      - combined_strength: relative lift/bodyweight metric
      - total_volume: sum of sets*reps*weight over past `days`
      - volume_percentile: % rank of user's volume among all users

    Returns dict of raw floats.
    """
    today = date.today()
    start_date = (today - timedelta(days=days)).isoformat()
    end_date = today.isoformat()

    combined_strength = get_combined_lift_strength_metric(user_id)

    # Total training volume
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
    total_volume = float(row[0] or 0.0)

    # Volume percentile
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
    if total_volume in volumes and volumes:
        rank = volumes.index(total_volume)
        volume_percentile = rank / len(volumes) * 100.0
    else:
        volume_percentile = 0.0

    return {
        "combined_strength": round(combined_strength, 3),
        "total_volume": round(total_volume, 2),
        "volume_percentile": round(volume_percentile, 1),
    }


def get_conditioning_metrics(user_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Raw conditioning metrics:
      - weekly_volume: sum of sets*reps*weight per day, summed over `days`
      - training_days: count of distinct workout days in `days`
      - volume_change_pct: % change vs prior `days` period
      - intensity_avg: total_volume / total_reps
      - consistency_pct: std dev of daily volumes as % of mean
      - avg_readiness: average readiness via external function

    Returns dict with raw values.
    """
    today = date.today()
    start_current = today - timedelta(days=days)
    prev_start = start_current - timedelta(days=days)

    # Daily volumes for current period
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

    daily_vols = [float(d[1] or 0.0) for d in days_data]
    total_reps = sum(int(d[2] or 0) for d in days_data) or 1

    weekly_volume = round(sum(daily_vols), 2)
    training_days = len(daily_vols)
    intensity_avg = round(weekly_volume / total_reps, 2)
    consistency_pct = (
        round(pstdev(daily_vols) / mean(daily_vols) * 100.0, 1) if daily_vols else 0.0
    )

    # Previous period volume
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
        prev_vol = float(cur.fetchone()[0] or 1.0)
    volume_change_pct = round((weekly_volume - prev_vol) / prev_vol * 100.0, 1)

    return {
        "weekly_volume": weekly_volume,
        "training_days": training_days,
        "volume_change_pct": volume_change_pct,
        "intensity_avg": intensity_avg,
        "consistency_pct": consistency_pct,
    }
