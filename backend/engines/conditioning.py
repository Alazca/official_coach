"""
Strength & Conditioning Engine Module for AI Weightlifting Assistant.

This module evaluates a user's strength and conditioning state against target profiles
and provides personalized feedback for improvement and visualization.
"""

import numpy as np
import datetime

from typing import Dict, List, Any, Tuple

from backend.engines.base_vector import (
    normalize,
    weighted_similarity,
    generate_vector_feedback,
)

from backend.database.db import get_target_profile

from backend.engines.exercise_recommendation import generate_exercise_recommendations


def evaluate_conditioning(
    user_input: Dict[str, float], profile_name: str = "default"
) -> Dict[str, Any]:
    """
    Evaluate user conditioning and return feedback + similarity score.

    Parameters:
        user_input (dict): e.g. {"sleep_quality": 7, "stress_level": 3, ...}

    Returns:
        dict: Similarity score, raw vector, normalized, feedback
    """
    dimensions, target_vector = get_target_profile(profile_name)

    # Convert input to ordered vector
    user_vec = np.array([user_input[dim] for dim in dimensions])
    user_vec_norm = normalize(user_vec)
    target_norm = normalize(target_vector)

    # Compute similarity
    similarity_score = weighted_similarity(user_vec_norm, target_norm)

    # Generate feedback
    feedback = generate_vector_feedback(user_vec, target_vector, dimensions)

    return {
        "raw_vector": user_vec.tolist(),
        "normalized_vector": user_vec_norm.tolist(),
        "similarity_score": round(similarity_score, 4),
        "feedback": feedback,
    }


def classify_strength_level(similarity_score: float) -> str:
    """
    Classify strength level based on similarity score.

    Parameters:
        similarity_score (float): Similarity score between 0 and 1

    Returns:
        str: Strength level classification
    """
    if similarity_score >= 0.9:
        return "Elite"
    elif similarity_score >= 0.75:
        return "Advanced"
    elif similarity_score >= 0.6:
        return "Intermediate"
    elif similarity_score >= 0.4:
        return "Novice"
    else:
        return "Beginner"


def classify_conditioning_level(similarity_score: float) -> str:
    """
    Classify conditioning level based on similarity score.

    Parameters:
        similarity_score (float): Similarity score between 0 and 1

    Returns:
        str: Conditioning level classification
    """
    if similarity_score >= 0.9:
        return "Elite"
    elif similarity_score >= 0.75:
        return "Advanced"
    elif similarity_score >= 0.6:
        return "Intermediate"
    elif similarity_score >= 0.4:
        return "Novice"
    else:
        return "Beginner"


def calculate_dimension_scores(
    user_vec: np.ndarray, target_vec: np.ndarray, dimension_labels: List[str]
) -> List[Dict[str, Any]]:
    """
    Calculate individual scores for each dimension.

    Parameters:
        user_vec (numpy.ndarray): User vector
        target_vec (numpy.ndarray): Target vector
        dimension_labels (List[str]): Labels for each dimension

    Returns:
        List of dimension scores
    """
    scores = []

    for i, label in enumerate(dimension_labels):
        # Calculate ratio of user value to target value
        if target_vec[i] > 0:
            ratio = min(user_vec[i] / target_vec[i], 1.0)
        else:
            ratio = 1.0 if user_vec[i] == 0 else 0.0

        # Convert ratio to percentage
        percentage = ratio * 100

        scores.append(
            {
                "dimension": label,
                "user_value": float(user_vec[i]),
                "target_value": float(target_vec[i]),
                "percentage": float(percentage),
                "ratio": float(ratio),
            }
        )

    return scores


def classify_overall_fitness(overall_score: float) -> str:
    """
    Classify overall fitness level based on combined score.

    Parameters:
        overall_score (float): Overall fitness score

    Returns:
        str: Overall fitness level classification
    """
    if overall_score >= 0.9:
        return "Elite"
    elif overall_score >= 0.8:
        return "Advanced"
    elif overall_score >= 0.65:
        return "Intermediate"
    elif overall_score >= 0.45:
        return "Novice"
    else:
        return "Beginner"
