from typing import Dict, List, Any


def generate_exercise_recommendations(
    priority_areas: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """
    Generate exercise recommendations based on priority areas.

    Parameters:
        priority_areas (List[Dict]): Priority areas for improvement

    Returns:
        Dict[str, List[str]]: Recommended exercises by dimension
    """
    # Exercise recommendations by dimension
    exercise_map = {
        # STRENGTH_DIMENSIONS
        "maximal_strength": ["Back Squats", "Deadlifts", "Bench Press"],
        "relative_strength": ["Pull-ups", "Pistol Squats", "Handstand Push-ups"],
        "explosive_strength": ["Power Cleans", "Snatch", "Jump Squats"],
        "strength_endurance": [
            "High-Rep Sets",
            "Kettlebell Swings",
            "Farmer's Carries",
        ],
        "agile_strength": [
            "Agility Ladder Drills",
            "Cone Drills with Resistance",
            "Loaded Carries",
        ],
        "speed_strength": [
            "Push Press",
            "Sprint Starts with Sled",
            "Medicine Ball Slams",
        ],
        "starting_strength": [
            "Box Squats",
            "Dead Start Deadlifts",
            "Paused Bench Press",
        ],
        # CONDITIONING_DIMENSIONS
        "cardiovascular_endurance": ["Zone 2 Running", "Cycling", "Swimming"],
        "muscle_strength": ["Dumbbell Press", "Barbell Rows", "Weighted Lunges"],
        "muscle_endurance": ["EMOM Workouts", "Circuit Training", "Bodyweight AMRAPs"],
        "flexibility": ["Dynamic Stretching", "PNF Stretching", "Yoga"],
        "body_composition": [
            "CrossFit-style WODs",
            "HIIT Circuits",
            "Full-Body Resistance Training",
        ],
    }

    recommendations = {}

    # Generate recommendations for each priority area
    for area in priority_areas:
        dimension = area["dimension"]
        if dimension in exercise_map:
            recommendations[dimension] = exercise_map[dimension]

    return recommendations


def generate_program_profile(
    strength_results: Dict[str, Any], conditioning_results: Dict[str, Any]
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
        "recommended_exercises": {},
    }

    # Add priority areas based on weaknesses
    for weakness in strength_results["weaknesses"]:
        program["priority_areas"].append(
            {
                "type": "strength",
                "dimension": weakness["dimension"],
                "importance": weakness["gap_score"],
            }
        )

    for weakness in conditioning_results["weaknesses"]:
        program["priority_areas"].append(
            {
                "type": "conditioning",
                "dimension": weakness["dimension"],
                "importance": weakness["gap_score"],
            }
        )

    # Sort priority areas by importance
    program["priority_areas"].sort(key=lambda x: x["importance"], reverse=True)

    # Limit to top 5 priority areas
    program["priority_areas"] = program["priority_areas"][:5]

    # Add exercise recommendations
    program["recommended_exercises"] = generate_exercise_recommendations(
        program["priority_areas"]
    )

    return program
