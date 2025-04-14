# conditioning_engine.py

import numpy as np
from engine.base_vector_engine import normalize, weighted_similarity, load_target_profile

def evaluate_conditioning(user_input: dict, weights: list = None) -> dict:
    """
    Compare user's conditioning state with the Head Coach's ideal conditioning profile.

    Parameters:
        user_input (dict): {
            "sleep_quality": 7,
            "stress_level": 3,
            "soreness": 2,
            "readiness": 8
        }
        weights (list): Optional weighting for influence factors.
    
    Returns:
        dict with similarity score and improvement suggestions
    """
    # Default weights if not provided
    weights = np.array(weights or [1, 1, 1, 1])

    # User vector
    user_vec = np.array([
        user_input["sleep_quality"],
        user_input["stress_level"],
        user_input["soreness"],
        user_input["readiness"]
    ])

    # Normalize
    user_vec = normalize(user_vec)

    # Load target vector
    target_vec = load_target_profile("head_coach_conditioning.json")
    target_vec = normalize(np.array(target_vec))

    # Similarity calculation (weighted cosine sim)
    similarity = weighted_similarity(user_vec, target_vec, weights)

    return {
        "similarity_score": float(similarity),
        "feedback": generate_feedback(user_vec, target_vec)
    }

