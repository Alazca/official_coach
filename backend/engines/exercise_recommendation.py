from typing import Dict, List, Any, Tuple

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

def generate_program_profile(
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
