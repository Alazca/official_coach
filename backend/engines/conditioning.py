"""
Strength & Conditioning Engine Module for AI Weightlifting Assistant.

This module evaluates a user's strength and conditioning state against target profiles
and provides personalized feedback for improvement and visualization.
"""

import numpy as np
import datetime
from typing import Dict, List, Union, Any, Tuple, Optional
from backend.engines.base_vector import (
    normalize, 
    weighted_similarity, 
    load_target_profile,
    generate_vector_feedback,
    vector_diff,
    vector_distance,
    interpolate_vectors
)
from backend.database.db_utils import (
    get_latest_checkin,
    save_readiness_score,
    update_checkin_with_readiness
)

# Define dimension labels for strength and conditioning vectors
STRENGTH_DIMENSIONS = [
    "maximal_strength",      # Highest weight lifted in a single effort
    "relative_strength",     # Strength in relation to body weight
    "explosive_strength",    # Maximum force in short period
    "strength_endurance",    # Sustain muscular effort over time
    "agile_strength",        # Strength while moving quickly
    "speed_strength",        # Generate strength quickly while moving
    "starting_strength"      # Ability to initiate movement with force
]

CONDITIONING_DIMENSIONS = [
    "cardiovascular_endurance",  # Oxygen delivery during sustained activity
    "muscle_strength",           # Muscle's ability to exert force for short period
    "muscle_endurance",          # Muscle's ability to contract repeatedly over time
    "flexibility",               # Range of motion in joints
    "body_composition"           # Ratio of muscle, bone, and fat
]


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
        return "Optimal"
    elif similarity_score >= 0.75:
        return "Good"
    elif similarity_score >= 0.6:
        return "Adequate"
    elif similarity_score >= 0.4:
        return "Suboptimal"
    else:
        return "Poor"


def identify_strengths_weaknesses(
    user_vec: np.ndarray, 
    target_vec: np.ndarray,
    dimension_labels: List[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Identify strengths and weaknesses from vector comparison.
    
    Parameters:
        user_vec (numpy.ndarray): User vector
        target_vec (numpy.ndarray): Target vector
        dimension_labels (List[str]): Labels for each dimension
        
    Returns:
        Tuple with lists of strengths and weaknesses
    """
    strengths = []
    weaknesses = []
    
    # Calculate differences for each dimension
    diffs = target_vec - user_vec
    
    # Sort dimensions by difference
    sorted_indices = np.argsort(diffs)
    
    # Top 3 strengths (dimensions where user exceeds or is closest to target)
    for idx in sorted_indices[:3]:
        # Only include as strength if within 10% of target or exceeding
        if diffs[idx] <= 0.1:
            strengths.append({
                "dimension": dimension_labels[idx],
                "user_value": float(user_vec[idx]),
                "target_value": float(target_vec[idx]),
                "difference": float(diffs[idx]),
                "gap_score": float(abs(diffs[idx]))
            })
    
    # Bottom 3 weaknesses (dimensions furthest below target)
    for idx in sorted_indices[-3:]:
        # Only include as weakness if more than 10% below target
        if diffs[idx] > 0.1:
            weaknesses.append({
                "dimension": dimension_labels[idx],
                "user_value": float(user_vec[idx]),
                "target_value": float(target_vec[idx]),
                "difference": float(diffs[idx]),
                "gap_score": float(abs(diffs[idx]))
            })
    
    return strengths, weaknesses


def calculate_dimension_scores(
    user_vec: np.ndarray,
    target_vec: np.ndarray,
    dimension_labels: List[str]
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
        
        scores.append({
            "dimension": label,
            "user_value": float(user_vec[i]),
            "target_value": float(target_vec[i]),
            "percentage": float(percentage),
            "ratio": float(ratio)
        })
    
    return scores


def generate_balanced_program(
    strength_results: Dict[str, Any],
    conditioning_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a balanced training program based on strength and conditioning comparisons.
    
    Parameters:
        strength_results (Dict[str, Any]): Strength evaluation results
        conditioning_results (Dict[str, Any]): Conditioning evaluation results
        
    Returns:
        Dict[str, Any]: Training program recommendations
    """
    # Calculate overall balance
    strength_score = strength_results["similarity_score"]
    conditioning_score = conditioning_results["similarity_score"]
    
    # Determine program focus based on relative scores
    if abs(strength_score - conditioning_score) < 0.1:
        program_focus = "balanced"
        strength_ratio = 0.5
        conditioning_ratio = 0.5
    elif strength_score < conditioning_score:
        program_focus = "strength_focused"
        # Calculate ratio based on difference, with more focus on weaker area
        difference = conditioning_score - strength_score
        strength_ratio = min(0.7, 0.5 + difference)
        conditioning_ratio = 1 - strength_ratio
    else:
        program_focus = "conditioning_focused"
        difference = strength_score - conditioning_score
        conditioning_ratio = min(0.7, 0.5 + difference)
        strength_ratio = 1 - conditioning_ratio
    
    # Compile program recommendations
    program = {
        "program_focus": program_focus,
        "strength_ratio": float(strength_ratio),
        "conditioning_ratio": float(conditioning_ratio),
        "priority_areas": [],
        "recommended_exercises": {}
    }
    
    # Add priority areas based on weaknesses
    for weakness in strength_results["weaknesses"]:
        program["priority_areas"].append({
            "type": "strength",
            "dimension": weakness["dimension"],
            "importance": weakness["gap_score"]
        })
    
    for weakness in conditioning_results["weaknesses"]:
        program["priority_areas"].append({
            "type": "conditioning",
            "dimension": weakness["dimension"],
            "importance": weakness["gap_score"]
        })
    
    # Sort priority areas by importance
    program["priority_areas"].sort(key=lambda x: x["importance"], reverse=True)
    
    # Limit to top 5 priority areas
    program["priority_areas"] = program["priority_areas"][:5]
    
    # Add exercise recommendations
    program["recommended_exercises"] = generate_exercise_recommendations(program["priority_areas"])
    
    return program


def generate_exercise_recommendations(priority_areas: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Generate exercise recommendations based on priority areas.
    
    Parameters:
        priority_areas (List[Dict]): Priority areas for improvement
        
    Returns:
        Dict[str, List[str]]: Recommended exercises by dimension
    """
    # Exercise recommendations by dimension
    exercise_map = {
        # Strength dimensions
        "squat_strength": ["Back Squats", "Front Squats", "Bulgarian Split Squats"],
        "bench_strength": ["Bench Press", "Incline Press", "Dumbbell Press"],
        "deadlift_strength": ["Conventional Deadlift", "Romanian Deadlift", "Trap Bar Deadlift"],
        "overhead_press": ["Military Press", "Push Press", "Dumbbell Shoulder Press"],
        "pull_up_capacity": ["Pull-ups", "Chin-ups", "Lat Pulldowns"],
        "core_strength": ["Planks", "Ab Rollouts", "Hanging Leg Raises"],
        
        # Conditioning dimensions
        "aerobic_capacity": ["Zone 2 Running", "Cycling", "Swimming"],
        "anaerobic_capacity": ["HIIT Sprints", "Tabata Intervals", "Battle Ropes"],
        "muscular_endurance": ["Circuit Training", "EMOM Workouts", "High-Rep Sets"],
        "recovery_rate": ["Active Recovery Sessions", "Mobility Work", "Light Cardio"],
        "work_capacity": ["CrossFit-style WODs", "Complex Barbell Circuits", "Supersets"],
        "movement_efficiency": ["Olympic Lifting Technique", "Plyometrics", "Agility Drills"]
    }
    
    recommendations = {}
    
    # Generate recommendations for each priority area
    for area in priority_areas:
        dimension = area["dimension"]
        if dimension in exercise_map:
            recommendations[dimension] = exercise_map[dimension]
    
    return recommendations


def prepare_visualization_data(
    strength_evaluation: Dict[str, Any],
    conditioning_evaluation: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare data for visualization in frontend.
    
    Parameters:
        strength_evaluation (Dict[str, Any]): Strength evaluation results
        conditioning_evaluation (Dict[str, Any]): Conditioning evaluation results
        
    Returns:
        Dict[str, Any]: Data structured for visualization
    """
    # Extract vector comparisons
    strength_comparison = strength_evaluation["vector_comparison"]
    conditioning_comparison = conditioning_evaluation["vector_comparison"]
    
    # Radar chart data for strength profile
    strength_chart_data = {
        "dimensions": strength_comparison["dimensions"],
        "user_values": strength_comparison["user"],
        "target_values": strength_comparison["target"]
    }
    
    # Radar chart data for conditioning profile
    conditioning_chart_data = {
        "dimensions": conditioning_comparison["dimensions"],
        "user_values": conditioning_comparison["user"],
        "target_values": conditioning_comparison["target"]
    }
    
    # Combined chart data with both profiles
    combined_chart_data = {
        "dimensions": strength_comparison["dimensions"] + conditioning_comparison["dimensions"],
        "user_values": strength_comparison["user"] + conditioning_comparison["user"],
        "target_values": strength_comparison["target"] + conditioning_comparison["target"]
    }
    
    # Progress data for bar charts
    progress_data = []
    
    # Add strength dimension scores
    for score in strength_evaluation["dimension_scores"]:
        progress_data.append({
            "dimension": score["dimension"],
            "category": "strength",
            "percentage": score["percentage"]
        })
    
    # Add conditioning dimension scores
    for score in conditioning_evaluation["dimension_scores"]:
        progress_data.append({
            "dimension": score["dimension"],
            "category": "conditioning",
            "percentage": score["percentage"]
        })
    
    return {
        "strength_chart": strength_chart_data,
        "conditioning_chart": conditioning_chart_data,
        "combined_chart": combined_chart_data,
        "progress_data": progress_data,
        "overall_scores": {
            "strength": strength_evaluation["similarity_score"],
            "conditioning": conditioning_evaluation["similarity_score"]
        }
    }


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