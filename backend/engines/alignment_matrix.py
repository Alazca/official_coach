"""
Alignment Matrix Module

This module provides functionality to evaluate user biometric and readiness data
to produce a readiness score and training recommendations.
"""
import sqlite3
import datetime
from typing import Dict, List, Any, Tuple

from backend.config.config import Config

def evaluate_vectors(user_input, user_id):
    """
    Evaluates the user's current biometric data against baseline metrics
    to determine readiness score and training recommendations.
    
    Args:
        user_input (dict): Dictionary containing user's current biometric data
            Keys include: weight, sleep_quality, stress_level, energy_level, soreness_level
        user_id (int): The user's ID to retrieve baseline and historical data
            
    Returns:
        dict: A dictionary containing the readiness score and recommendations
    """
    # Initialize the result dictionary
    result = {
        "readiness_score": 0,
        "recommendations": []
    }
    
    try:
        # Calculate readiness score based on the input data
        # Scale: 0-100 where higher is better readiness
        
        # Extract metrics from user input
        sleep = user_input.get("sleep_quality", 5)  # Scale 1-10
        stress = user_input.get("stress_level", 5)  # Scale 1-10
        energy = user_input.get("energy_level", 5)  # Scale 1-10
        soreness = user_input.get("soreness_level", 5)  # Scale 1-10
        
        # Calculate base readiness score - weighted average of inputs
        # Sleep and energy are positive indicators (higher is better)
        # Stress and soreness are negative indicators (lower is better)
        readiness_score = (
            (sleep * 0.3) +             # 30% weight for sleep quality
            ((10 - stress) * 0.25) +    # 25% weight for stress (inverted)
            (energy * 0.25) +           # 25% weight for energy
            ((10 - soreness) * 0.2)     # 20% weight for soreness (inverted)
        ) * 10  # Scale to 0-100
        
        # Adjust readiness based on recent activity and recovery patterns
        recovery_adjustment = get_recovery_adjustment(user_id)
        readiness_score += recovery_adjustment
        
        # Ensure score is within bounds (0-100)
        readiness_score = max(0, min(100, readiness_score))
        
        # Generate recommendations based on readiness score
        recommendations = generate_recommendations(readiness_score, user_input)
        
        # Update result dictionary
        result["readiness_score"] = round(readiness_score, 1)
        result["recommendations"] = recommendations
        
        return result
        
    except Exception as e:
        # Log error and return minimal result with default value
        print(f"Error in evaluate_vectors: {str(e)}")
        result["readiness_score"] = 50  # Default middle score
        result["recommendations"] = ["Unable to generate specific recommendations due to an error."]
        return result

def get_recovery_adjustment(user_id):
    """
    Analyzes recent activity and recovery patterns to adjust the readiness score.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        float: Adjustment value for readiness score (-10 to +10)
    """
    try:  
        # For now, return a neutral adjustment
        return 0
        
    except Exception as e:
        print(f"Error in get_recovery_adjustment: {str(e)}")
        return 0  # Neutral adjustment in case of error

def generate_recommendations(readiness_score, user_input):
    """
    Generates training and recovery recommendations based on readiness score.
    
    Args:
        readiness_score (float): The calculated readiness score (0-100)
        user_input (dict): User's current biometric data
        
    Returns:
        list: List of recommendation strings
    """
    recommendations = []
    
    # Categorize readiness
    if readiness_score >= 80:
        recommendations.append("High readiness: You're well-recovered and ready for a challenging workout.")
        recommendations.append("Consider high-intensity or heavy strength training today.")
    
    elif readiness_score >= 60:
        recommendations.append("Good readiness: You're in good recovery state for moderate training.")
        recommendations.append("Moderate intensity workouts or technical skill work recommended.")
    
    elif readiness_score >= 40:
        recommendations.append("Moderate readiness: Some fatigue present, approach training cautiously.")
        recommendations.append("Consider light to moderate training with focus on technique.")
    
    else:
        recommendations.append("Low readiness: Recovery is priority. Your body needs rest.")
        recommendations.append("Active recovery or rest day recommended.")
    
    # Add specific recommendations based on individual metrics
    sleep = user_input.get("sleep_quality", 5)
    if sleep < 4:
        recommendations.append("Poor sleep detected. Consider sleep hygiene improvements and limit high-intensity exercise.")
    
    stress = user_input.get("stress_level", 5)
    if stress > 7:
        recommendations.append("High stress detected. Stress-reducing activities like yoga or light cardio may be beneficial.")
    
    soreness = user_input.get("soreness_level", 5)
    if soreness > 7:
        recommendations.append("High muscle soreness detected. Focus on recovery modalities like stretching, foam rolling, or light movement.")
    
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