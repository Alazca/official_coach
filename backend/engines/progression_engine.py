"""
Progression Engine Module

This module provides functionality to analyze workout performance over time,
track progress metrics, and generate insights and recommendations for progression.
"""

import sqlite3
import datetime
import numpy as np
from backend.config.config import Config
from backend.database.db import create_conn, get_workout_history


def calculate_volume_progression(user_id: int, time_frame: str = "month") -> float:
    """
    Calculates the progression in workout volume (sets * reps * weight).

    Args:
        user_id (int): User ID
        time_frame (str): 'week', 'month', 'quarter', or 'year'

    Returns:
        float: Volume progression score (0-100)
    """
    try:
        workout_history = get_workout_history(user_id, time_frame)

        if not workout_history or len(workout_history) < 2:
            return 50  # Neutral score for insufficient data

        # Group workouts by workout type and extract volume metrics
        volumes_by_type = {}
        for workout in workout_history:
            workout_type = workout["workout_type"]
            if workout_type not in volumes_by_type:
                volumes_by_type[workout_type] = []

            # Calculate volume for this workout (simplified)
            volume = workout.get("total_volume", 0)
            if volume == 0:
                # Calculate from exercise details if available
                exercises = workout.get("exercises", [])
                for exercise in exercises:
                    sets = exercise.get("sets", 0)
                    reps = exercise.get("reps", 0)
                    weight = exercise.get("weight", 0)
                    volume += sets * reps * weight

            volumes_by_type[workout_type].append(volume)

        # Calculate progression for each workout type
        progression_scores = []
        for workout_type, volumes in volumes_by_type.items():
            if len(volumes) < 2:
                continue

            # Calculate moving average to smooth out variations
            window_size = min(3, len(volumes))
            recent_avg = sum(volumes[:window_size]) / window_size
            past_avg = sum(volumes[-window_size:]) / window_size

            if past_avg > 0:
                percent_change = (recent_avg - past_avg) / past_avg * 100
                # Map percent change to a 0-100 score with 0% change = 50
                progression_score = 50 + (
                    percent_change * 2.5
                )  # 10% increase = 75 score
                progression_scores.append(max(0, min(100, progression_score)))

        # Average the scores from different workout types
        if progression_scores:
            return sum(progression_scores) / len(progression_scores)
        else:
            return 50  # Neutral score

    except Exception as e:
        print(f"Error in calculate_volume_progression: {str(e)}")
        return 50  # Neutral score in case of error


def calculate_intensity_progression(user_id: int, time_frame: str = "month"):
    """
    Evaluates how workout intensity has progressed over time.

    Derives a trend from intensity metrics such as heart rate, RPE, or weight %.

    Args:
        user_id (int): ID of the user
        time_frame (str): Analysis window

    Returns:
        float: Intensity progression score (0-100)
    """

    try:
        workout_history = get_workout_history(user_id, time_frame)

        if not workout_history or len(workout_history) < 2:
            return 50  # Neutral score for insufficient data

        # Extract intensity metrics from workouts
        intensities = []
        for workout in workout_history:
            # Use reported intensity or calculate from workout data
            intensity = workout.get("intensity", 0)
            if intensity == 0:
                # Calculate from heart rate, weight percentages, or RPE if available
                avg_hr = workout.get("average_heart_rate", 0)
                rpe = workout.get("rpe", 0)
                max_weight_pct = workout.get("max_weight_percentage", 0)

                if avg_hr > 0:
                    intensity += avg_hr / 2  # Scale heart rate to approximate intensity
                if rpe > 0:
                    intensity += rpe * 10  # Scale RPE (typically 1-10) to 0-100
                if max_weight_pct > 0:
                    intensity += max_weight_pct  # Weight percentage already 0-100

                # Average the available metrics
                divisor = sum(1 for x in (avg_hr, rpe, max_weight_pct) if x > 0)
                intensity = intensity / divisor if divisor > 0 else 50

            intensities.append(intensity)

        # Calculate progression trend
        if len(intensities) < 3:
            # Simple comparison for few data points
            recent = intensities[0]
            past = intensities[-1]
            percent_change = (recent - past) / past * 100 if past > 0 else 0
        else:
            # Use linear regression for trend with more data points
            x = np.array(range(len(intensities)))
            y = np.array(intensities)
            slope, _ = np.polyfit(x, y, 1)
            percent_change = slope * 10  # Scale slope to percentage

        # Map percent change to a 0-100 score with 0% change = 50
        progression_score = 50 + (percent_change * 2)  # 25% increase = 100 score
        return max(0, min(100, progression_score))

    except Exception as e:
        print(f"Error in calculate_intensity_progression: {str(e)}")
        return 50  # Neutral score in case of error


def get_fitness_level(user_id: int, time_frame: str = "month") -> str:
    """
    Determines the user's fitness level based on workout frequency.

    Args:
        user_id (int): The user's ID
        time_frame (str): Time period to evaluate

    Returns:
        str: 'beginner', 'intermediate', or 'advanced'
    """
    try:

        frequency = calculate_workout_frequency(user_id, time_frame)
        if frequency >= 3.5:
            return "advanced"
        elif frequency >= 2:
            return "intermediate"
        else:
            return "beginner"
    except Exception as e:
        print(f"Error in get_fitness_level: {e}")
        return "beginner"  # Default fallback


def calculate_consistency_score(user_id: int, time_frame: str = "month") -> float:
    """
    Calculates how consistent the user has been with their planned workouts.

    Pulls user workout history and compares actual sessions vs expected frequency.

    Args:
        user_id (int): ID of the user
        time_frame (str): Period for analysis

    Returns:
        float: Consistency score from 0 to 100
    """

    conn = None
    cursor = None

    try:

        workout_history = get_workout_history(user_id, time_frame)
        if not workout_history:
            return 0  # No workouts = no consistency

        # Determine expected workout frequency
        conn = create_conn()
        cursor = conn.cursor()

        # Get user's planned workout days per week
        query = "SELECT planned_workout_days FROM user_plans WHERE user_id = ?"
        cursor.execute(query, (workout_history[0]["user_id"],))
        result = cursor.fetchone()
        planned_days_per_week = (
            result["planned_workout_days"] if result else 3
        )  # Default to 3 days/week

        # Calculate days in the selected time frame
        days_in_period = {"week": 7, "month": 30, "quarter": 90, "year": 365}.get(
            time_frame, 30
        )

        # Calculate expected workouts in the period
        expected_workouts = (days_in_period / 7) * planned_days_per_week

        # Calculate actual vs expected ratio
        actual_workouts = len(workout_history)
        consistency_ratio = min(1.0, actual_workouts / expected_workouts)

        # Scale to 0-100
        consistency_score = consistency_ratio * 100

        return consistency_score

    except Exception as e:
        print(f"Error in calculate_consistency_score: {str(e)}")
        return 50  # Neutral score in case of error


def calculate_workout_frequency(user_id: int, time_frame: str = "month"):
    """
    Calculates average workout frequency.

    Args:
        user_id: ID of user
        time_frame (str): Time period for analysis

    Returns:
        float: Average workouts per week
    """
    try:
        workout_history = get_workout_history(user_id, time_frame)
        if not workout_history:
            return 0

        days_in_period = {"week": 7, "month": 30, "quarter": 90, "year": 365}.get(
            time_frame, 30
        )

        workout_count = len(workout_history)
        weeks_in_period = days_in_period / 7

        return workout_count / weeks_in_period

    except Exception as e:
        print(f"Error in calculate_workout_frequency: {str(e)}")
        return 0


def calculate_strength_progression(user_id: int, time_frame: str = "month"):
    """
    Calculates strength progression from key lifts.

    Args:
        workout_history (list): List of workout records

    Returns:
        dict: Strength progression by exercise
    """
    try:
        workout_history = get_workout_history(user_id, time_frame)
        if not workout_history:
            return {}

        # Key strength exercises to track
        key_exercises = ["squat", "bench press", "deadlift", "overhead press", "row"]
        strength_progression = {}

        # Extract max weights for key exercises
        for exercise_name in key_exercises:
            weights = []
            dates = []

            for workout in workout_history:
                exercises = workout.get("exercises", [])
                for exercise in exercises:
                    if exercise_name.lower() in exercise.get("name", "").lower():
                        weight = exercise.get("weight", 0)
                        if weight > 0:
                            weights.append(weight)
                            dates.append(workout.get("workout_date"))

            if weights and len(weights) >= 2:
                initial = weights[-1]
                current = weights[0]
                change_pct = ((current - initial) / initial * 100) if initial > 0 else 0

                strength_progression[exercise_name] = {
                    "initial": initial,
                    "current": current,
                    "change_percentage": round(change_pct, 1),
                    "trend": (
                        "increasing"
                        if change_pct > 0
                        else "decreasing" if change_pct < 0 else "stable"
                    ),
                }

        return strength_progression

    except Exception as e:
        print(f"Error in calculate_strength_progression: {str(e)}")
        return {}


def calculate_endurance_progression(user_id: int, time_frame: str = "month"):
    """
    Calculates endurance progression from cardio workouts.

    Args:
        workout_history (list): List of workout records

    Returns:
        dict: Endurance progression metrics
    """
    try:
        workout_history = get_workout_history(user_id, time_frame)
        if not workout_history:
            return {}

        # Filter for cardio workouts
        cardio_workouts = [
            w
            for w in workout_history
            if w.get("workout_type", "").lower()
            in ["cardio", "running", "cycling", "swimming", "hiit"]
        ]

        if not cardio_workouts or len(cardio_workouts) < 2:
            return {}

        # Extract metrics
        durations = []
        distances = []
        avg_heart_rates = []

        for workout in cardio_workouts:
            durations.append(workout.get("duration", 0))
            distances.append(workout.get("distance", 0))
            avg_heart_rates.append(workout.get("average_heart_rate", 0))

        # Calculate progression
        endurance_metrics = {}

        # Duration progression
        if all(durations):
            initial_duration = durations[-1]
            current_duration = durations[0]
            duration_change = (
                ((current_duration - initial_duration) / initial_duration * 100)
                if initial_duration > 0
                else 0
            )
            endurance_metrics["duration"] = {
                "initial": initial_duration,
                "current": current_duration,
                "change_percentage": round(duration_change, 1),
            }

        # Distance progression
        if all(distances):
            initial_distance = distances[-1]
            current_distance = distances[0]
            distance_change = (
                ((current_distance - initial_distance) / initial_distance * 100)
                if initial_distance > 0
                else 0
            )
            endurance_metrics["distance"] = {
                "initial": initial_distance,
                "current": current_distance,
                "change_percentage": round(distance_change, 1),
            }

        # Heart rate efficiency (lower is better for same workload)
        if all(avg_heart_rates):
            initial_hr = avg_heart_rates[-1]
            current_hr = avg_heart_rates[0]
            hr_change = (
                ((initial_hr - current_hr) / initial_hr * 100) if initial_hr > 0 else 0
            )
            endurance_metrics["heart_rate_efficiency"] = {
                "initial": initial_hr,
                "current": current_hr,
                "change_percentage": round(hr_change, 1),
            }

        return endurance_metrics

    except Exception as e:
        print(f"Error in calculate_endurance_progression: {str(e)}")
        return {}


def generate_progression_insights(
    workout_history, volume_progression, intensity_progression, consistency_score
):
    """
    Generates insights about the user's workout progression.

    Args:
        workout_history (list): List of workout records
        volume_progression (float): Volume progression score
        intensity_progression (float): Intensity progression score
        consistency_score (float): Consistency score

    Returns:
        list: List of insight strings
    """
    insights = []

    # Volume insights
    if volume_progression >= 70:
        insights.append(
            "Your workout volume is steadily increasing, showing good progress in training capacity."
        )
    elif volume_progression <= 30:
        insights.append(
            "Your workout volume has been decreasing, which may indicate fatigue or insufficient recovery."
        )
    else:
        insights.append("Your workout volume is relatively stable.")

    # Intensity insights
    if intensity_progression >= 70:
        insights.append(
            "Your workout intensity is trending upward, indicating improved strength and conditioning."
        )
    elif intensity_progression <= 30:
        insights.append(
            "Your workout intensity has been decreasing, which may require attention to training stimulus."
        )
    else:
        insights.append(
            "Your workout intensity is being maintained at a consistent level."
        )

    # Consistency insights
    if consistency_score >= 80:
        insights.append(
            "Excellent workout consistency! Your adherence to your training schedule is a key factor in your results."
        )
    elif consistency_score >= 60:
        insights.append(
            "Good workout consistency overall, with room for minor improvements in schedule adherence."
        )
    elif consistency_score >= 40:
        insights.append(
            "Moderate workout consistency. Try to improve adherence to your planned schedule for better results."
        )
    else:
        insights.append(
            "Your workout consistency needs improvement. Consider addressing schedule barriers."
        )

    # Workout type distribution
    workout_types = {}
    for workout in workout_history:
        workout_type = workout.get("workout_type", "unknown")
        workout_types[workout_type] = workout_types.get(workout_type, 0) + 1

    dominant_type = (
        max(workout_types.items(), key=lambda x: x[1])[0] if workout_types else None
    )
    if dominant_type:
        insights.append(
            f"Your training is primarily focused on {dominant_type} workouts."
        )

    # Check for balance
    if len(workout_types) == 1 and workout_types:
        insights.append(
            "Your training lacks variety. Consider incorporating different workout types for more balanced results."
        )

    return insights


def generate_progression_recommendations(progression_score, workout_history):
    """
    Generates training recommendations based on progression analysis.

    Args:
        progression_score (float): Overall progression score
        workout_history (list): List of workout records

    Returns:
        list: List of recommendation strings
    """
    recommendations = []

    # Progression-based recommendations
    if progression_score >= 80:
        recommendations.append(
            "Your progression is excellent. Consider setting more challenging goals to continue advancement."
        )
        recommendations.append(
            "Try incorporating advanced techniques like periodization to further optimize progress."
        )

    elif progression_score >= 60:
        recommendations.append(
            "Your progression is good. Focus on consistency and gradual intensity increases."
        )
        recommendations.append(
            "Consider tracking additional performance metrics to identify specific areas for improvement."
        )

    elif progression_score >= 40:
        recommendations.append(
            "Your progression is moderate. Review your training program for potential optimization."
        )
        recommendations.append(
            "Focus on progressive overload by gradually increasing volume or intensity each week."
        )

    else:
        recommendations.append(
            "Your progression needs attention. Consider revising your training approach."
        )
        recommendations.append(
            "Focus first on consistency, then gradually build volume before increasing intensity."
        )

    # Check for plateaus
    if workout_history and len(workout_history) >= 4:
        # Check if recent workouts show stagnation in key metrics
        recent_volumes = [w.get("total_volume", 0) for w in workout_history[:3]]
        recent_intensities = [w.get("intensity", 0) for w in workout_history[:3]]

        volume_stagnant = (
            all(
                abs(v - recent_volumes[0]) < recent_volumes[0] * 0.05
                for v in recent_volumes
            )
            if all(recent_volumes)
            else False
        )
        intensity_stagnant = (
            all(abs(i - recent_intensities[0]) < 5 for i in recent_intensities)
            if all(recent_intensities)
            else False
        )

        if volume_stagnant and intensity_stagnant:
            recommendations.append(
                "You appear to be plateauing. Consider introducing variation through new exercises or training methods."
            )
            recommendations.append(
                "A deload week followed by a change in program may help break through your plateau."
            )

    # Check workout frequency
    workout_dates = [w.get("workout_date") for w in workout_history]
    if workout_dates and len(workout_dates) >= 2:
        date_diffs = [
            (workout_dates[i - 1] - workout_dates[i]).days
            for i in range(1, len(workout_dates))
        ]
        avg_days_between = sum(date_diffs) / len(date_diffs) if date_diffs else 0

        if avg_days_between > 4:
            recommendations.append(
                "Your workout frequency is low. Consider increasing training frequency for better results."
            )
        elif avg_days_between < 1.5:
            recommendations.append(
                "Your workout frequency is very high. Ensure you're getting adequate recovery between sessions."
            )

    return recommendations


def suggest_progression_plan(user_id: int, target_goal: str) -> dict:
    """
    Suggests a progression plan based on user's history and target goal.

    Args:
        user_id (int): The user's ID
        target_goal (str): The user's target goal (e.g., 'strength', 'hypertrophy', 'endurance')

    Returns:
        dict: A structured progression plan
    """
    try:
        # Initialize result
        result = {
            "plan_name": f"{target_goal.capitalize()} Progression Plan",
            "duration_weeks": 8,
            "phases": [],
            "weekly_targets": [],
            "success_metrics": [],
        }

        # Get workout history
        workout_history = get_workout_history(user_id, "month")

        # Determine starting point based on history
        if not workout_history:
            fitness_level = "beginner"
        else:
            # Get workout frequency using user_id (history is fetched inside)
            workout_frequency = calculate_workout_frequency(user_id, "month")
            if workout_frequency >= 3.5:
                fitness_level = "advanced"
            elif workout_frequency >= 2:
                fitness_level = "intermediate"
            else:
                fitness_level = "beginner"

        # Create phased approach based on goal and fitness level
        if target_goal == "strength":
            result["phases"] = create_strength_phases(fitness_level)
            result["success_metrics"] = [
                "1RM increases in compound lifts",
                "Volume progression",
                "Technical proficiency",
            ]

        elif target_goal == "hypertrophy":
            result["phases"] = create_hypertrophy_phases(fitness_level)
            result["success_metrics"] = [
                "Muscle measurements",
                "Progressive overload in target rep ranges",
                "Mind-muscle connection",
            ]

        elif target_goal == "endurance":
            result["phases"] = create_endurance_phases(fitness_level)
            result["success_metrics"] = [
                "Distance covered",
                "Heart rate recovery time",
                "Perceived exertion decreases",
            ]

        elif target_goal == "fat_loss":
            result["phases"] = create_fat_loss_phases(fitness_level)
            result["success_metrics"] = [
                "Body composition changes",
                "Work capacity improvements",
                "Resting heart rate",
            ]

        # Generate weekly targets
        result["weekly_targets"] = generate_weekly_targets(
            target_goal, fitness_level, result["duration_weeks"]
        )

        return result

    except Exception as e:
        print(f"Error in suggest_progression_plan: {str(e)}")
        return {
            "plan_name": "Basic Progression Plan",
            "duration_weeks": 4,
            "phases": [
                {
                    "name": "Building consistency",
                    "focus": "Establishing workout routine",
                }
            ],
            "weekly_targets": ["Complete all scheduled workouts"],
            "success_metrics": ["Workout adherence"],
        }


def create_strength_phases(fitness_level):
    """Helper function to create strength training phases"""
    if fitness_level == "beginner":
        return [
            {
                "name": "Foundation",
                "duration_weeks": 2,
                "focus": "Movement patterns and technique",
            },
            {
                "name": "Base strength",
                "duration_weeks": 3,
                "focus": "Progressive loading with moderate weights",
            },
            {
                "name": "Strength development",
                "duration_weeks": 3,
                "focus": "Increasing intensity with adequate recovery",
            },
        ]
    elif fitness_level == "intermediate":
        return [
            {
                "name": "Hypertrophy block",
                "duration_weeks": 3,
                "focus": "Volume accumulation to build muscle",
            },
            {
                "name": "Strength block",
                "duration_weeks": 3,
                "focus": "Increasing intensity with moderate volume",
            },
            {
                "name": "Peak strength",
                "duration_weeks": 2,
                "focus": "High intensity, lower volume for maximal strength",
            },
        ]
    else:  # advanced
        return [
            {
                "name": "Volume accumulation",
                "duration_weeks": 2,
                "focus": "High volume to drive adaptation",
            },
            {
                "name": "Strength accumulation",
                "duration_weeks": 2,
                "focus": "Progressive loading with moderate volume",
            },
            {
                "name": "Intensity phase",
                "duration_weeks": 2,
                "focus": "High intensity work to maximize strength",
            },
            {
                "name": "Peak/taper",
                "duration_weeks": 2,
                "focus": "Reduced volume, maintained intensity for peaking",
            },
        ]


def create_hypertrophy_phases(fitness_level):
    """Helper function to create hypertrophy training phases"""
    if fitness_level == "beginner":
        return [
            {
                "name": "Movement patterns",
                "duration_weeks": 2,
                "focus": "Learning exercises and technique",
            },
            {
                "name": "Base volume",
                "duration_weeks": 3,
                "focus": "Building workload capacity",
            },
            {
                "name": "Hypertrophy development",
                "duration_weeks": 3,
                "focus": "Increased volume in hypertrophy ranges",
            },
        ]
    elif fitness_level == "intermediate":
        return [
            {
                "name": "Metabolic phase",
                "duration_weeks": 2,
                "focus": "Higher reps, shorter rest periods",
            },
            {
                "name": "Volume phase",
                "duration_weeks": 3,
                "focus": "Moderate reps with increased sets",
            },
            {
                "name": "Tension phase",
                "duration_weeks": 3,
                "focus": "Focus on time under tension and mind-muscle connection",
            },
        ]
    else:  # advanced
        return [
            {
                "name": "Primer phase",
                "duration_weeks": 1,
                "focus": "Preparing muscles for growth stimulus",
            },
            {
                "name": "Volume block",
                "duration_weeks": 3,
                "focus": "Accumulating volume across varying rep ranges",
            },
            {
                "name": "Intensification",
                "duration_weeks": 2,
                "focus": "Increased load with maintained volume",
            },
            {
                "name": "Specialization",
                "duration_weeks": 2,
                "focus": "Focus on lagging muscle groups",
            },
        ]


def create_endurance_phases(fitness_level):
    """Helper function to create endurance training phases"""
    if fitness_level == "beginner":
        return [
            {
                "name": "Base building",
                "duration_weeks": 3,
                "focus": "Building aerobic capacity",
            },
            {
                "name": "Endurance development",
                "duration_weeks": 3,
                "focus": "Increasing duration of steady state work",
            },
            {
                "name": "Mixed endurance",
                "duration_weeks": 2,
                "focus": "Introducing intensity variations",
            },
        ]
    elif fitness_level == "intermediate":
        return [
            {
                "name": "Aerobic base",
                "duration_weeks": 2,
                "focus": "Building aerobic efficiency",
            },
            {
                "name": "Threshold work",
                "duration_weeks": 3,
                "focus": "Improving lactate threshold",
            },
            {
                "name": "Mixed zones",
                "duration_weeks": 3,
                "focus": "Training across different heart rate zones",
            },
        ]
    else:  # advanced
        return [
            {
                "name": "Aerobic accumulation",
                "duration_weeks": 2,
                "focus": "Building aerobic capacity",
            },
            {
                "name": "Threshold development",
                "duration_weeks": 2,
                "focus": "Improving lactate threshold and clearance",
            },
            {
                "name": "VO2 max development",
                "duration_weeks": 2,
                "focus": "High intensity intervals for maximal oxygen uptake",
            },
            {
                "name": "Specific endurance",
                "duration_weeks": 2,
                "focus": "Sport-specific endurance patterns",
            },
        ]


def create_fat_loss_phases(fitness_level):
    """Helper function to create fat loss training phases"""
    if fitness_level == "beginner":
        return [
            {
                "name": "Movement foundation",
                "duration_weeks": 2,
                "focus": "Building movement capacity and consistency",
            },
            {
                "name": "Volume introduction",
                "duration_weeks": 3,
                "focus": "Gradually increasing workout density",
            },
            {
                "name": "Metabolic conditioning",
                "duration_weeks": 3,
                "focus": "Increasing caloric expenditure through conditioning",
            },
        ]
    elif fitness_level == "intermediate":
        return [
            {
                "name": "Base building",
                "duration_weeks": 2,
                "focus": "Building work capacity and consistency",
            },
            {
                "name": "Metabolic phase",
                "duration_weeks": 3,
                "focus": "HIIT and circuit training for caloric burn",
            },
            {
                "name": "Strength maintenance",
                "duration_weeks": 3,
                "focus": "Preserving muscle while emphasizing fat loss",
            },
        ]
    else:  # advanced
        return [
            {
                "name": "Metabolic primer",
                "duration_weeks": 1,
                "focus": "Preparing for increased workload",
            },
            {
                "name": "High volume phase",
                "duration_weeks": 2,
                "focus": "Maximum caloric expenditure through volume",
            },
            {
                "name": "Intensity phase",
                "duration_weeks": 2,
                "focus": "HIIT and metabolic resistance training",
            },
            {
                "name": "Recovery conditioning",
                "duration_weeks": 1,
                "focus": "Active recovery while maintaining deficit",
            },
            {
                "name": "Peak intensity",
                "duration_weeks": 2,
                "focus": "Maximum intensity methods for final results",
            },
        ]


def generate_weekly_targets(goal, fitness_level, duration_weeks):
    """
    Generates weekly progression targets based on goal and fitness level.

    Args:
        goal (str): Training goal
        fitness_level (str): User's fitness level
        duration_weeks (int): Program duration in weeks

    Returns:
        list: Weekly targets for the progression plan
    """
    weekly_targets = []

    # Base progression rates by fitness level
    if fitness_level == "beginner":
        progression_rate = 0.05  # 5% per week for beginners
    elif fitness_level == "intermediate":
        progression_rate = 0.03  # 3% per week for intermediates
    else:
        progression_rate = 0.015  # 1.5% per week for advanced

    # Generate weekly targets based on goal
    for week in range(1, duration_weeks + 1):
        cumulative_progression = (1 + progression_rate) ** (week - 1)

        if goal == "strength":
            if week == 1:
                weekly_targets.append(
                    f"Week {week}: Establish baseline 1RMs for key lifts"
                )
            else:
                percentage = round((cumulative_progression - 1) * 100, 1)
                weekly_targets.append(
                    f"Week {week}: Target {percentage}% increase in working weights from baseline"
                )

        elif goal == "hypertrophy":
            if week == 1:
                weekly_targets.append(
                    f"Week {week}: Establish baseline training volume"
                )
            else:
                if week % 4 == 0:
                    weekly_targets.append(
                        f"Week {week}: Deload week - reduce volume by 40%, maintain intensity"
                    )
                else:
                    percentage = round((cumulative_progression - 1) * 100, 1)
                    weekly_targets.append(
                        f"Week {week}: Increase training volume by {percentage}% from baseline"
                    )

        elif goal == "endurance":
            if week == 1:
                weekly_targets.append(
                    f"Week {week}: Establish baseline distance and duration"
                )
            else:
                percentage = round((cumulative_progression - 1) * 100, 1)
                weekly_targets.append(
                    f"Week {week}: Increase training distance by {percentage}% from baseline"
                )

        elif goal == "fat_loss":
            if week == 1:
                weekly_targets.append(
                    f"Week {week}: Establish baseline workout density (work completed per minute)"
                )
            else:
                percentage = round((cumulative_progression - 1) * 100, 1)
                weekly_targets.append(
                    f"Week {week}: Increase workout density by {percentage}% from baseline"
                )

    return weekly_targets


def analyze_progression(user_id, time_frame: str = "month"):
    """
    Analyzes the user's workout progression over a specified time frame.

    Args:
        user_id (int): The user's ID to retrieve workout history
        time_frame (str): The period for analysis: 'week', 'month', 'quarter', or 'year'

    Returns:
        dict: A dictionary containing progression metrics and insights
    """
    # Initialize the result dictionary
    result = {
        "progression_score": 0,
        "metrics": {},
        "insights": [],
        "recommendations": [],
    }

    try:
        # Get historical workout data
        workout_history = get_workout_history(user_id, time_frame)

        if not workout_history:
            result["insights"].append(
                "Insufficient workout data for progression analysis."
            )
            result["recommendations"].append(
                "Complete more workouts to enable progression tracking."
            )
            return result

        # Calculate progression metrics
        volume_progression = calculate_volume_progression(user_id, time_frame)
        intensity_progression = calculate_intensity_progression(user_id, time_frame)
        consistency_score = calculate_consistency_score(user_id, time_frame)

        # Calculate overall progression score (0-100)
        progression_score = (
            (volume_progression * 0.35)  # 35% weight for volume progression
            + (intensity_progression * 0.35)  # 35% weight for intensity progression
            + (consistency_score * 0.3)  # 30% weight for consistency
        )

        # Ensure score is within bounds (0-100)
        progression_score = max(0, min(100, progression_score))

        # Generate insights and recommendations
        insights = generate_progression_insights(
            workout_history,
            volume_progression,
            intensity_progression,
            consistency_score,
        )
        recommendations = generate_progression_recommendations(
            progression_score, workout_history
        )

        # Compile metrics for detailed analysis
        metrics = {
            "volume_progression": volume_progression,
            "intensity_progression": intensity_progression,
            "consistency_score": consistency_score,
            "workout_frequency": calculate_workout_frequency(user_id, time_frame),
            "strength_gains": calculate_strength_progression(user_id, time_frame),
            "endurance_gains": calculate_endurance_progression(user_id, time_frame),
        }

        # Update result dictionary
        result["progression_score"] = round(progression_score, 1)
        result["metrics"] = metrics
        result["insights"] = insights
        result["recommendations"] = recommendations

        return result

    except Exception as e:
        # Log error and return minimal result with default value
        print(f"Error in analyze_progression: {str(e)}")
        result["insights"].append("Error analyzing workout progression.")
        result["recommendations"].append(
            "Try again later or contact support if the issue persists."
        )
        return result
