"""
Base Vector Engine Module for AI Weightlifting Assistant.

This module provides core vector operations and similarity calculations
that serve as the foundation for various attribute engines in the system.
"""

import sqlite3
import numpy as np
import json
import os
from typing import List, Dict, Union, Tuple, Any


def normalize(vector: np.ndarray) -> np.ndarray:
    """
    Normalize a vector to unit length.

    Parameters:
        vector (numpy.ndarray): Input vector to normalize

    Returns:
        numpy.ndarray: Normalized vector
    """

    norm = np.linalg.norm(vector)
    # Prevent division by zero

    if norm == 0:
        return vector
    return vector / norm


def weighted_similarity(
    vec1: np.ndarray, vec2: np.ndarray, weights: np.ndarray = None
) -> float:
    """
    Calculate weighted cosine similarity between two vectors.

    Parameters:
        vec1 (numpy.ndarray): First vector
        vec2 (numpy.ndarray): Second vector
        weights (numpy.ndarray): Optional weight vector for each dimension

    Returns:
        float: Similarity score between 0 and 1
    """

    if weights is not None:
        # Apply weights
        weights = normalize(weights)  # Normalize weights
        vec1 = vec1 * weights
        vec2 = vec2 * weights

    # Calculate cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    # Prevent division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    # Ensure the result is within bounds due to potential floating-point errors
    similarity = max(min(similarity, 1.0), -1.0)

    # Convert to 0-1 range
    return (similarity + 1) / 2 if similarity < 0 else similarity


def vector_diff(vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
    """
    Calculate the difference between two vectors.

    Parameters:
        vec1 (numpy.ndarray): First vector
        vec2 (numpy.ndarray): Second vector

    Returns:
        numpy.ndarray: Difference vector
    """
    return vec2 - vec1


def vector_distance(
    vec1: np.ndarray, vec2: np.ndarray, method: str = "euclidean"
) -> float:
    """
    Calculate distance between two vectors using various metrics.

    Parameters:
        vec1 (numpy.ndarray): First vector
        vec2 (numpy.ndarray): Second vector
        method (str): Distance method ('euclidean', 'manhattan', 'chebyshev')

    Returns:
        float: Distance value
    """
    if method == "euclidean":
        return np.linalg.norm(vec1 - vec2)
    elif method == "manhattan":
        return np.sum(np.abs(vec1 - vec2))
    elif method == "chebyshev":
        return np.max(np.abs(vec1 - vec2))
    else:
        raise ValueError(f"Unknown distance method: {method}")


def vector_to_percentile(vec: np.ndarray, reference_matrix: np.ndarray) -> np.ndarray:
    """
    Convert vector values to percentiles based on reference data.

    Parameters:
        vec (numpy.ndarray): Input vector
        reference_matrix (numpy.ndarray): Matrix of reference vectors

    Returns:
        numpy.ndarray: Vector with values converted to percentiles
    """
    percentiles = np.zeros_like(vec, dtype=float)

    for i in range(len(vec)):
        # Extract the i-th column from reference matrix
        reference_values = reference_matrix[:, i]
        # Calculate the percentile of vec[i] in reference_values
        percentiles[i] = (
            np.sum(reference_values <= vec[i]) / len(reference_values) * 100
        )

    return percentiles


def generate_vector_feedback(
    user_vec: np.ndarray,
    target_vec: np.ndarray,
    dimension_labels: List[str],
    threshold: float = 0.2,
) -> List[Dict[str, Any]]:
    """
    Generate detailed feedback based on vector comparison.

    Parameters:
        user_vec (numpy.ndarray): User's vector
        target_vec (numpy.ndarray): Target vector
        dimension_labels (List[str]): Names for each vector dimension
        threshold (float): Difference threshold to trigger feedback

    Returns:
        List[Dict[str, Any]]: Detailed feedback with dimension name,
                              difference magnitude, and actionable suggestion
    """
    feedback = []
    dimensions = dimension_labels

    for i, label in enumerate(dimensions):
        diff = target_vec[i] - user_vec[i]

        if abs(diff) > threshold:
            direction = "increase" if diff > 0 else "decrease"
            magnitude = "significantly" if abs(diff) > threshold * 2 else "slightly"

            feedback_item = {
                "dimension": label,
                "current_value": float(user_vec[i]),
                "target_value": float(target_vec[i]),
                "difference": float(diff),
                "direction": direction,
                "magnitude": magnitude,
                "suggestion": f"{magnitude.capitalize()} {direction} your {label.replace('_', ' ')}",
            }

            feedback.append(feedback_item)

    return feedback


def interpolate_vectors(
    vec1: np.ndarray, vec2: np.ndarray, ratio: float = 0.5
) -> np.ndarray:
    """
    Interpolate between two vectors based on a ratio.

    Parameters:
        vec1 (numpy.ndarray): First vector (ratio=0.0)
        vec2 (numpy.ndarray): Second vector (ratio=1.0)
        ratio (float): Interpolation ratio between 0 and 1

    Returns:
        numpy.ndarray: Interpolated vector
    """
    ratio = max(0.0, min(1.0, ratio))  # Clamp ratio between 0 and 1
    return vec1 * (1 - ratio) + vec2 * ratio


def aggregate_vectors(vectors: List[np.ndarray], method: str = "mean") -> np.ndarray:
    """
    Aggregate multiple vectors into one using various methods.

    Parameters:
        vectors (List[np.ndarray]): List of vectors to aggregate
        method (str): Aggregation method ('mean', 'median', 'min', 'max')

    Returns:
        numpy.ndarray: Aggregated vector
    """
    if not vectors:
        raise ValueError("Cannot aggregate empty list of vectors")

    # Stack vectors into a matrix
    matrix = np.vstack(vectors)

    if method == "mean":
        return np.mean(matrix, axis=0)
    elif method == "median":
        return np.median(matrix, axis=0)
    elif method == "min":
        return np.min(matrix, axis=0)
    elif method == "max":
        return np.max(matrix, axis=0)
    else:
        raise ValueError(f"Unknown aggregation method: {method}")


def vector_stats(vectors: List[np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Calculate statistical measures for a set of vectors.

    Parameters:
        vectors (List[np.ndarray]): List of vectors

    Returns:
        Dict[str, np.ndarray]: Statistical measures (mean, std, min, max)
    """
    if not vectors:
        raise ValueError("Cannot calculate stats on empty list of vectors")

    # Stack vectors into a matrix
    matrix = np.vstack(vectors)

    return {
        "mean": np.mean(matrix, axis=0),
        "std": np.std(matrix, axis=0),
        "min": np.min(matrix, axis=0),
        "max": np.max(matrix, axis=0),
        "median": np.median(matrix, axis=0),
        "count": len(vectors),
    }
