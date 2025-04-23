"""
send_to_db.py
Aggregates outputs from all evaluation engines and updates the database accordingly.
"""

from backend.engines.conditioning import evaluate_conditioning
from backend.engines.progression_engine import evaluate_progression
from backend.engines.workout_engine import evaluate_workout_effectiveness
from backend.database.db import (
    save_readiness_score,
    update_checkin_with_readiness,
    save_fitness_analysis,
    get_latest_checkin
)
import numpy as np
import datetime


def evaluate_and_store_all(user_id: int, user_input: dict, profile_name: str = "default") -> None:
    # 1. Evaluate Conditioning
    conditioning_result = evaluate_conditioning(user_input, profile_name)
    conditioning_score = conditioning_result["similarity_score"]

    # 2. Evaluate Progression (e.g. strength progression over time)
    progression_result = evaluate_progression(user_id)
    strength_score = progression_result["progression_score"]

    # 3. Evaluate Workout Effectiveness (e.g. how effective the last workout was)
    workout_result = evaluate_workout_effectiveness(user_id)
    workout_score = workout_result["effectiveness_score"]

    # 4. Aggregate Overall Score
    overall_score = np.mean([conditioning_score, strength_score, workout_score])

    # 5. Classify levels (optional if you're displaying it somewhere)
    from backend.engines.conditioning import classify_conditioning_level, classify_strength_level, classify_overall_fitness

    fitness_level = classify_overall_fitness(overall_score)

    # 6. Save Readiness Score
    readiness_data = {
        "user_id": user_id,
        "readiness_score": int(conditioning_score * 100),
        "contributing_factors": str(conditioning_result["feedback"]),
        "readiness_date": datetime.date.today().isoformat(),
        "source": "Auto",
        "alignment_score": None,
        "overtraining_score": None
    }
    readiness_id = save_readiness_score(readiness_data)

    # 7. Link to latest check-in
    update_checkin_with_readiness(checkin_id=get_latest_checkin(user_id), readiness_id=readiness_id)

    # 8. Save Full Fitness Analysis
    analysis_data = {
        "user_id": user_id,
        "analysis_date": datetime.date.today().isoformat(),
        "strength_score": strength_score,
        "conditioning_score": conditioning_score,
        "overall_score": overall_score,
        "fitness_level": fitness_level,
        "analysis_data": {
            "conditioning": conditioning_result,
            "progression": progression_result,
            "workout": workout_result
        }
    }
    save_fitness_analysis(analysis_data)

