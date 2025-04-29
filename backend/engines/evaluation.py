"""
Vector Evaluation Engine

Compares the user conditioning vector to the current target vector
and returns a similarity score for feedback or visualization.
"""

import numpy as np
from backend.engines.base_vector_math import weighted_similarity, normalize


def evaluate_vector_alignment(
    user_vector: np.ndarray, target_vector: np.ndarray, weights: np.ndarray = None
) -> dict:
    """
    Compare user vs. target vector and return similarity score.

    Parameters:
        user_vector (np.ndarray): Vector representing user's current state
        target_vector (np.ndarray): Goal-adjusted, interpolated target vector
        weights (np.ndarray): Optional weights for each dimension

    Returns:
        dict: {
            "similarity_score": float (0.0 to 1.0)
        }
    """
    user_vec_norm = normalize(user_vector)
    target_vec_norm = normalize(target_vector)

    sim = weighted_similarity(user_vec_norm, target_vec_norm, weights)
    return {"similarity_score": round(sim, 4)}
