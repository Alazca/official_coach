# nutrition_engine.py
from typing import Dict, Any
import numpy as np
from backend.engines.base_vector import weighted_similarity, generate_vector_feedback, normalize
from backend.database.db import get_target_profile

def evaluate_nutrition_input(user_input: Dict[str, float],
                             profile_name: str = "default",
                             date: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluate user nutrition and return feedback + similarity score.

    Parameters:
        user_input (dict): e.g. {"calories": 2200, "protein": 140, "carbs": 280, ...}
        profile_name (str): Name of the nutrition profile to fetch
        date (str, optional): Date string for this evaluation

    Returns:
        dict: {
            "date": date,
            "raw_vector": [...],
            "normalized_vector": [...],
            "similarity_score": 0.0000,
            "feedback": {...}
        }
    """
    # Fetch profile dims + vector just like conditioning does
    dimensions, target_vector = get_target_profile(profile_name)

    # Build input vector in the same order
    input_vec = np.array([user_input.get(dim, 0) for dim in dimensions])
    input_vec_norm = normalize(input_vec)
    target_norm = normalize(np.array(target_vector))

    # Compute similarity and generate feedback
    similarity_score = weighted_similarity(input_vec_norm, target_norm)
    feedback = generate_vector_feedback(input_vec, target_vector, dimensions, threshold=0.1)

    return {
        "date": date,
        "raw_vector": input_vec.tolist(),
        "normalized_vector": input_vec_norm.tolist(),
        "similarity_score": round(similarity_score, 4),
        "feedback": feedback
    }
