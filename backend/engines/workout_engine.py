"""
Workout Engine Module

This module provides functionality to generate personalized workout recommendations
based on user fitness metrics, goals, and historical performance data.
"""
import sqlite3
import datetime
import random
from backend.config.config import Config
from backend.database.db import get_workout_history

def generate_workout(user_data, user_id):
    """
    Generates a personalized workout plan based on user's fitness metrics,
    goals, history and available equipment.
    
    Args:
        user_data (dict): Dictionary containing user's current fitness data
            Keys may include: fitness_level, available_equipment, target_muscle_groups,
            workout_duration, workout_goal, energy_level
        user_id (int): The user's ID to retrieve historical workout data
            
    Returns:
        dict: A dictionary containing the workout plan and recommendations
    """
    # Initialize the result dictionary
    result = {
        "workout_plan": [],
        "intensity_level": "",
        "estimated_duration": 0,
        "calories_burn_estimate": 0,
        "notes": []
    }
    
    try:
        # Extract metrics from user input
        fitness_level = user_data.get("fitness_level", "intermediate")  # beginner, intermediate, advanced
        available_equipment = user_data.get("available_equipment", ["bodyweight"])  # list of available equipment
        target_muscle_groups = user_data.get("target_muscle_groups", ["full_body"])  # list of muscle groups
        workout_duration = user_data.get("workout_duration", 45)  # desired workout length in minutes
        workout_goal = user_data.get("workout_goal", "general_fitness")  # strength, hypertrophy, endurance, etc.
        energy_level = user_data.get("energy_level", 7)  # scale 1-10
        
        # Adjust workout variables based on energy level and recent workouts
        intensity_modifier = determine_intensity(energy_level, user_id)
        rest_needs = analyze_recovery_needs(user_id)
        
        # Generate the workout plan
        workout_plan = build_workout_plan(
            fitness_level, 
            available_equipment, 
            target_muscle_groups, 
            workout_duration, 
            workout_goal,
            intensity_modifier,
            rest_needs
        )
        
        # Calculate workout metrics
        intensity_level = calculate_intensity_level(workout_plan, fitness_level)
        estimated_duration = estimate_duration(workout_plan)
        calories_burn_estimate = estimate_calories(workout_plan, user_id)
        
        # Generate additional notes and recommendations
        notes = generate_workout_notes(workout_plan, rest_needs, user_id)
        
        # Update result dictionary
        result["workout_plan"] = workout_plan
        result["intensity_level"] = intensity_level
        result["estimated_duration"] = estimated_duration
        result["calories_burn_estimate"] = calories_burn_estimate
        result["notes"] = notes
        
        return result
        
    except Exception as e:
        # Log error and return minimal result with default value
        print(f"Error in generate_workout: {str(e)}")
        default_workout = create_default_workout(fitness_level="beginner")
        result["workout_plan"] = default_workout
        result["intensity_level"] = "moderate"
        result["estimated_duration"] = 30
        result["calories_burn_estimate"] = 200
        result["notes"] = ["Default workout generated due to an error."]
        return result

def determine_intensity(energy_level, user_id):
    """
    Determines appropriate workout intensity based on user's energy level
    and workout history.
    
    Args:
        energy_level (int): User's reported energy level (1-10)
        user_id (int): User ID for retrieving workout history
        
    Returns:
        float: Intensity modifier (0.7-1.3) where 1.0 is normal intensity
    """
    # Base intensity on energy level
    base_intensity = energy_level / 10  # Scale to 0.1-1.0
    
    # In a full implementation, we would analyze:
    # 1. Recent workout intensities
    # 2. Training periodization cycle
    # 3. User's stated goals
    
    # Scale to appropriate range (0.7-1.3)
    intensity_modifier = 0.7 + (base_intensity * 0.6)
    
    return intensity_modifier

def analyze_recovery_needs(user_id):
    """
    Analyzes user's workout history to determine which muscle groups
    need rest and recovery.
    
    Args:
        user_id (int): User ID for retrieving workout history
        
    Returns:
        dict: Dictionary of muscle groups and their recovery status
    """
    # In a real implementation, this would:
    # 1. Query recent workouts from database
    # 2. Analyze which muscle groups were trained recently
    # 3. Calculate appropriate rest periods based on intensity
    
    # Mock implementation for demonstration
    recovery_status = {
        "chest": "recovered",
        "back": "recovered",
        "legs": "needs_rest",
        "shoulders": "recovered",
        "arms": "needs_rest",
        "core": "recovered"
    }
    
    return recovery_status

def build_workout_plan(fitness_level, equipment, muscle_groups, duration, goal, intensity, recovery_status):
    """
    Builds a complete workout plan based on user parameters.
    
    Args:
        fitness_level (str): User's fitness level
        equipment (list): Available equipment
        muscle_groups (list): Target muscle groups
        duration (int): Desired workout duration in minutes
        goal (str): Workout goal (strength, hypertrophy, etc.)
        intensity (float): Intensity modifier
        recovery_status (dict): Recovery status of muscle groups
        
    Returns:
        list: List of workout exercises with sets, reps, and rest periods
    """
    # In a real implementation, this would:
    # 1. Query exercise database for appropriate exercises
    # 2. Filter based on available equipment
    # 3. Select exercises for target muscle groups
    # 4. Arrange exercises in optimal order
    # 5. Assign appropriate sets, reps, and rest periods based on goal
    
    # Mock implementation for demonstration
    workout_plan = []
    
    # Generate workout based on fitness level and goal
    if "full_body" in muscle_groups:
        if fitness_level == "beginner":
            workout_plan = generate_beginner_full_body(equipment, goal, intensity)
        elif fitness_level == "intermediate":
            workout_plan = generate_intermediate_full_body(equipment, goal, intensity)
        else:  # advanced
            workout_plan = generate_advanced_full_body(equipment, goal, intensity)
    else:
        # Handle specific muscle group focus
        workout_plan = generate_split_workout(muscle_groups, equipment, fitness_level, goal, intensity, recovery_status)
    
    # Adjust workout length to match desired duration
    workout_plan = adjust_workout_length(workout_plan, duration)
    
    return workout_plan

def generate_beginner_full_body(equipment, goal, intensity):
    """Generates a beginner-friendly full body workout"""
    workout = []
    
    # Compound movements first
    if "barbell" in equipment:
        workout.append({
            "exercise": "Barbell Squats",
            "sets": 3,
            "reps": "8-10",
            "rest": 90,
            "muscle_group": "legs"
        })
    else:
        workout.append({
            "exercise": "Bodyweight Squats",
            "sets": 3,
            "reps": "12-15",
            "rest": 60,
            "muscle_group": "legs"
        })
    
    if "barbell" in equipment:
        workout.append({
            "exercise": "Bench Press",
            "sets": 3,
            "reps": "8-10",
            "rest": 90,
            "muscle_group": "chest"
        })
    elif "dumbbells" in equipment:
        workout.append({
            "exercise": "Dumbbell Press",
            "sets": 3,
            "reps": "10-12",
            "rest": 60,
            "muscle_group": "chest"
        })
    else:
        workout.append({
            "exercise": "Push-ups",
            "sets": 3,
            "reps": "As many as possible",
            "rest": 60,
            "muscle_group": "chest"
        })
    
    # More exercises...
    workout.append({
        "exercise": "Plank",
        "sets": 3,
        "reps": "30-60 seconds",
        "rest": 45,
        "muscle_group": "core"
    })
    
    # Adjust for intensity
    for exercise in workout:
        if intensity > 1.1:  # High intensity
            exercise["sets"] = min(exercise["sets"] + 1, 5)
        elif intensity < 0.9:  # Lower intensity
            exercise["sets"] = max(exercise["sets"] - 1, 2)
    
    return workout

def generate_intermediate_full_body(equipment, goal, intensity):
    """Generates an intermediate-level full body workout"""
    # Similar implementation to beginner but with more advanced exercises
    workout = []
    
    # Sample exercises for intermediate
    if "barbell" in equipment:
        workout.append({
            "exercise": "Barbell Squats",
            "sets": 4,
            "reps": "6-8",
            "rest": 120,
            "muscle_group": "legs"
        })
    
    if "dumbbells" in equipment:
        workout.append({
            "exercise": "Dumbbell Romanian Deadlift",
            "sets": 3,
            "reps": "8-10",
            "rest": 90,
            "muscle_group": "legs"
        })
    
    workout.append({
        "exercise": "Pull-ups",
        "sets": 3,
        "reps": "6-10",
        "rest": 90,
        "muscle_group": "back"
    })
    
    # More intermediate exercises...
    
    # Adjust for intensity
    for exercise in workout:
        if intensity > 1.1:
            exercise["sets"] += 1
            exercise["rest"] -= 15
        elif intensity < 0.9:
            exercise["rest"] += 30
    
    return workout

def generate_advanced_full_body(equipment, goal, intensity):
    """Generates an advanced full body workout"""
    # Implementation for advanced workouts
    workout = []
    
    # Sample exercises for advanced
    workout.append({
        "exercise": "Barbell Back Squats",
        "sets": 5,
        "reps": "5-5-3-3-1",
        "rest": 180,
        "muscle_group": "legs"
    })
    
    # More advanced exercises...
    
    return workout

def generate_split_workout(muscle_groups, equipment, fitness_level, goal, intensity, recovery_status):
    """Generates a split workout focusing on specific muscle groups"""
    workout = []
    
    # Filter out muscle groups that need rest
    target_muscles = [muscle for muscle in muscle_groups 
                     if muscle in recovery_status and recovery_status[muscle] != "needs_rest"]
    
    # If all targeted muscles need rest, recommend alternative
    if not target_muscles and muscle_groups:
        return [{
            "exercise": "Active Recovery",
            "sets": 1,
            "reps": "20-30 minutes",
            "rest": 0,
            "muscle_group": "cardiovascular",
            "notes": "All target muscle groups need rest. Try some light cardio instead."
        }]
    
    # Generate exercises for each muscle group
    for muscle in target_muscles:
        if muscle == "chest":
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Barbell Bench Press",
                    "sets": 4,
                    "reps": "8-10",
                    "rest": 90,
                    "muscle_group": "chest"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Dumbbell Press",
                    "sets": 4,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "chest"
                })
            else:
                workout.append({
                    "exercise": "Push-ups",
                    "sets": 3,
                    "reps": "As many as possible",
                    "rest": 60,
                    "muscle_group": "chest"
                })
                
            # Add a second chest exercise for variety
            if "cable" in equipment:
                workout.append({
                    "exercise": "Cable Flyes",
                    "sets": 3,
                    "reps": "12-15",
                    "rest": 60,
                    "muscle_group": "chest"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Dumbbell Flyes",
                    "sets": 3,
                    "reps": "12-15",
                    "rest": 60,
                    "muscle_group": "chest"
                })
                
        elif muscle == "back":
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Barbell Rows",
                    "sets": 4,
                    "reps": "8-10",
                    "rest": 90,
                    "muscle_group": "back"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Single-Arm Dumbbell Rows",
                    "sets": 3,
                    "reps": "10-12 each arm",
                    "rest": 60,
                    "muscle_group": "back"
                })
            else:
                workout.append({
                    "exercise": "Pull-ups",
                    "sets": 3,
                    "reps": "8-10",
                    "rest": 90,
                    "muscle_group": "back"
                })
                
            # Add a second back exercise
            if "cable" in equipment:
                workout.append({
                    "exercise": "Lat Pulldowns",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "back"
                })
            elif "bodyweight" in equipment:
                workout.append({
                    "exercise": "Inverted Rows",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "back"
                })
                
        elif muscle == "legs":
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Squats",
                    "sets": 4,
                    "reps": "8-10",
                    "rest": 120,
                    "muscle_group": "legs"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Dumbbell Lunges",
                    "sets": 3,
                    "reps": "10-12 each leg",
                    "rest": 60,
                    "muscle_group": "legs"
                })
            else:
                workout.append({
                    "exercise": "Lunges",
                    "sets": 3,
                    "reps": "12-15 each leg",
                    "rest": 60,
                    "muscle_group": "legs"
                })
                
            # Add a second leg exercise
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Romanian Deadlifts",
                    "sets": 3,
                    "reps": "8-10",
                    "rest": 90,
                    "muscle_group": "legs"
                })
            elif "bodyweight" in equipment:
                workout.append({
                    "exercise": "Bulgarian Split Squats",
                    "sets": 3,
                    "reps": "10-12 each leg",
                    "rest": 60,
                    "muscle_group": "legs"
                })
        
        elif muscle == "shoulders":
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Overhead Press",
                    "sets": 4,
                    "reps": "8-10",
                    "rest": 90,
                    "muscle_group": "shoulders"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Dumbbell Shoulder Press",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "shoulders"
                })
            else:
                workout.append({
                    "exercise": "Pike Push-ups",
                    "sets": 3,
                    "reps": "As many as possible",
                    "rest": 60,
                    "muscle_group": "shoulders"
                })
                
            # Add lateral raises for more shoulder development
            if "dumbbells" in equipment:
                workout.append({
                    "exercise": "Lateral Raises",
                    "sets": 3,
                    "reps": "12-15",
                    "rest": 45,
                    "muscle_group": "shoulders"
                })
            else:
                workout.append({
                    "exercise": "Lateral Plank Raises",
                    "sets": 3,
                    "reps": "10-12 each side",
                    "rest": 45,
                    "muscle_group": "shoulders"
                })
                
        elif muscle == "arms":
            # Biceps
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Barbell Curls",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "arms"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Dumbbell Curls",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "arms"
                })
            else:
                workout.append({
                    "exercise": "Chin-ups",
                    "sets": 3,
                    "reps": "As many as possible",
                    "rest": 60,
                    "muscle_group": "arms"
                })
                
            # Triceps
            if "barbell" in equipment:
                workout.append({
                    "exercise": "Skull Crushers",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "arms"
                })
            elif "dumbbells" in equipment:
                workout.append({
                    "exercise": "Tricep Extensions",
                    "sets": 3,
                    "reps": "10-12",
                    "rest": 60,
                    "muscle_group": "arms"
                })
            else:
                workout.append({
                    "exercise": "Diamond Push-ups",
                    "sets": 3,
                    "reps": "As many as possible",
                    "rest": 60,
                    "muscle_group": "arms"
                })
                
        elif muscle == "core":
            workout.append({
                "exercise": "Plank",
                "sets": 3,
                "reps": "30-60 seconds",
                "rest": 45,
                "muscle_group": "core"
            })
            
            workout.append({
                "exercise": "Russian Twists",
                "sets": 3,
                "reps": "15-20 each side",
                "rest": 45,
                "muscle_group": "core"
            })
            
            if fitness_level != "beginner":
                workout.append({
                    "exercise": "Hanging Leg Raises",
                    "sets": 3,
                    "reps": "10-15",
                    "rest": 60,
                    "muscle_group": "core"
                })
                
        elif muscle == "cardio" or muscle == "cardiovascular":
            workout.append({
                "exercise": "Interval Sprints",
                "sets": 5,
                "reps": "30 seconds on, 30 seconds off",
                "rest": 30,
                "muscle_group": "cardiovascular"
            })
            
            if "equipment" in equipment and "gym" in equipment:
                workout.append({
                    "exercise": "Rowing Machine",
                    "sets": 1,
                    "reps": "10-15 minutes",
                    "rest": 0,
                    "muscle_group": "cardiovascular"
                })
            else:
                workout.append({
                    "exercise": "Jumping Jacks",
                    "sets": 3,
                    "reps": "45 seconds",
                    "rest": 15,
                    "muscle_group": "cardiovascular"
                })
        
        # Default case for any unspecified muscle groups
        else:
            workout.append({
                "exercise": f"General {muscle.capitalize()} Exercise",
                "sets": 3,
                "reps": "12-15",
                "rest": 60,
                "muscle_group": muscle
            })
    
    # Adjust workout based on goal
    if goal == "strength":
        for exercise in workout:
            if "reps" in exercise and isinstance(exercise["reps"], str) and "-" in exercise["reps"]:
                # For strength training, use lower rep ranges with higher rest
                low, high = exercise["reps"].split("-")
                new_low = max(4, int(low) - 2)
                new_high = max(6, int(high) - 4)
                exercise["reps"] = f"{new_low}-{new_high}"
                exercise["rest"] = min(180, exercise["rest"] + 30)
    
    elif goal == "hypertrophy":
        # For hypertrophy, use moderate rep ranges
        # This is already the default in most exercises
        pass
    
    elif goal == "endurance":
        for exercise in workout:
            if "reps" in exercise and isinstance(exercise["reps"], str) and "-" in exercise["reps"]:
                # For endurance, use higher rep ranges with lower rest
                low, high = exercise["reps"].split("-")
                new_low = int(low) + 5
                new_high = int(high) + 5
                exercise["reps"] = f"{new_low}-{new_high}"
                exercise["rest"] = max(30, exercise["rest"] - 15)
    
    # Apply intensity modifier
    for exercise in workout:
        if intensity > 1.1:  # High intensity
            exercise["sets"] = min(5, exercise["sets"] + 1)
        elif intensity < 0.9:  # Lower intensity
            exercise["sets"] = max(2, exercise["sets"] - 1)
    
    return workout

def adjust_workout_length(workout_plan, target_duration):
    """
    Adjusts the workout plan to match the target duration
    
    Args:
        workout_plan (list): The current workout plan
        target_duration (int): Target duration in minutes
        
    Returns:
        list: Adjusted workout plan
    """
    # Estimate current workout duration
    current_duration = 0
    for exercise in workout_plan:
        # Calculate time for each exercise (sets * reps * time per rep + rest between sets)
        sets = exercise["sets"]
        rest_time = exercise["rest"] * (sets - 1)  # Rest between sets
        
        # Estimate time per set (30 seconds to 1 minute depending on exercise)
        exercise_time = sets * 45  # 45 seconds per set on average
        
        # Add to total duration
        current_duration += (exercise_time + rest_time)
    
    # Convert from seconds to minutes
    current_duration = current_duration / 60
    
    # If current duration is close enough to target, return as is
    if abs(current_duration - target_duration) <= 5:
        return workout_plan
    
    # If workout is too long, remove exercises
    if current_duration > target_duration:
        # Sort exercises by importance (keep compound movements)
        compound_exercises = []
        isolation_exercises = []
        
        for exercise in workout_plan:
            # Simple classification - better implementation would use a database
            if exercise["exercise"] in ["Squats", "Deadlifts", "Bench Press", "Pull-ups", "Barbell Rows"]:
                compound_exercises.append(exercise)
            else:
                isolation_exercises.append(exercise)
        
        # Rebuild workout prioritizing compound exercises
        adjusted_workout = compound_exercises.copy()
        
        # Add isolation exercises until we approach target duration
        estimated_duration = sum([ex["sets"] * 45 + ex["rest"] * (ex["sets"] - 1) for ex in adjusted_workout]) / 60
        
        for exercise in isolation_exercises:
            # Calculate how much time this exercise would add
            exercise_duration = (exercise["sets"] * 45 + exercise["rest"] * (exercise["sets"] - 1)) / 60
            
            # Add if it doesn't push us over the target
            if estimated_duration + exercise_duration <= target_duration:
                adjusted_workout.append(exercise)
                estimated_duration += exercise_duration
        
        return adjusted_workout
    
    # If workout is too short, add exercises or increase sets
    else:
        # Determine how much time to add
        time_to_add = target_duration - current_duration
        
        # If we need to add significant time, add more exercises
        if time_to_add > 10:
            # Add supplementary exercises based on muscle groups already in workout
            muscle_groups_in_workout = set([ex["muscle_group"] for ex in workout_plan])
            
            for muscle_group in muscle_groups_in_workout:
                # Add supplementary exercise for this muscle group
                if muscle_group == "chest":
                    workout_plan.append({
                        "exercise": "Cable Flyes",
                        "sets": 3,
                        "reps": "12-15",
                        "rest": 60,
                        "muscle_group": "chest"
                    })
                elif muscle_group == "back":
                    workout_plan.append({
                        "exercise": "Lat Pulldowns",
                        "sets": 3,
                        "reps": "12-15",
                        "rest": 60,
                        "muscle_group": "back"
                    })
                # More supplementary exercises for other muscle groups...
                
                # Recalculate duration to see if we're close enough
                new_duration = sum([ex["sets"] * 45 + ex["rest"] * (ex["sets"] - 1) for ex in workout_plan]) / 60
                if abs(new_duration - target_duration) <= 5:
                    break
        
        # If we only need to add a little time, increase sets for existing exercises
        else:
            for exercise in workout_plan:
                if time_to_add <= 0:
                    break
                
                # Add one set
                exercise["sets"] += 1
                
                # Recalculate how much time we've added
                time_added = (45 + exercise["rest"]) / 60  # One set + rest in minutes
                time_to_add -= time_added
        
        return workout_plan

def calculate_intensity_level(workout_plan, fitness_level):
    """
    Calculates the overall intensity level of a workout plan.
    
    Args:
        workout_plan (list): The workout plan
        fitness_level (str): User's fitness level
        
    Returns:
        str: Descriptive intensity level (light, moderate, intense, very intense)
    """
    # No workout means no intensity
    if not workout_plan:
        return "none"
    
    # Calculate average intensity scores
    total_intensity = 0
    
    for exercise in workout_plan:
        # Base intensity score
        intensity_score = 0
        
        # Higher sets means higher intensity
        sets = exercise["sets"]
        intensity_score += sets * 0.5
        
        # Compound movements are more intense
        compound_exercises = ["Squats", "Deadlifts", "Bench Press", "Pull-ups", "Barbell Rows"]
        if any(comp in exercise["exercise"] for comp in compound_exercises):
            intensity_score += 2
        
        # Shorter rest periods mean higher intensity
        rest_period = exercise["rest"]
        if rest_period <= 30:
            intensity_score += 3
        elif rest_period <= 60:
            intensity_score += 2
        elif rest_period <= 90:
            intensity_score += 1
        
        # Add to total
        total_intensity += intensity_score
    
    # Calculate average
    avg_intensity = total_intensity / len(workout_plan)
    
    # Adjust based on fitness level (same workout is more intense for a beginner)
    if fitness_level == "beginner":
        avg_intensity *= 1.5
    elif fitness_level == "intermediate":
        avg_intensity *= 1.2
    
    # Convert to descriptive intensity
    if avg_intensity < 3:
        return "light"
    elif avg_intensity < 5:
        return "moderate"
    elif avg_intensity < 7:
        return "intense"
    else:
        return "very intense"

def estimate_duration(workout_plan):
    """
    Estimates the total duration of a workout in minutes.
    
    Args:
        workout_plan (list): The workout plan
        
    Returns:
        int: Estimated duration in minutes
    """
    if not workout_plan:
        return 0
    
    total_duration_seconds = 0
    
    for exercise in workout_plan:
        sets = exercise["sets"]
        rest_seconds = exercise["rest"] * (sets - 1)  # Rest between sets
        
        # Estimate time per set based on exercise type
        time_per_set_seconds = 45  # Default 45 seconds per set
        
        # Adjust for specific exercises that take longer
        if "Deadlift" in exercise["exercise"]:
            time_per_set_seconds = 60
        
        # Calculate total time for this exercise
        exercise_seconds = (sets * time_per_set_seconds) + rest_seconds
        
        # Add to total
        total_duration_seconds += exercise_seconds
    
    # Add time for warm-up and cool-down
    warm_up_seconds = 300  # 5 minutes
    cool_down_seconds = 300  # 5 minutes
    
    total_duration_seconds += warm_up_seconds + cool_down_seconds
    
    # Convert to minutes and round up
    total_duration_minutes = round(total_duration_seconds / 60)
    
    return total_duration_minutes

def estimate_calories(workout_plan, user_id):
    """
    Estimates calories burned during the workout.
    
    Args:
        workout_plan (list): The workout plan
        user_id (int): User ID to retrieve user metrics
        
    Returns:
        int: Estimated calories burned
    """
    # In a real implementation, we would retrieve user's weight, age, gender
    # For now, we'll use average values
    avg_weight_kg = 75  # Average weight in kg
    calories_per_minute = {
        "light": 3,      # 3 calories per minute for light intensity
        "moderate": 5,   # 5 calories per minute for moderate intensity
        "intense": 7,    # 7 calories per minute for intense workouts
        "very intense": 10  # 10 calories per minute for very intense workouts
    }
    
    # Calculate workout duration
    duration_minutes = estimate_duration(workout_plan)
    
    # Determine workout intensity
    intensity = calculate_intensity_level(workout_plan, "intermediate")  # Default to intermediate
    
    # Calculate calories burned
    calories_burned = duration_minutes * calories_per_minute.get(intensity, 5)
    
    # Adjust based on exercise type (weights vs cardio)
    weight_training_exercises = sum(1 for ex in workout_plan if "cardio" not in ex.get("muscle_group", ""))
    cardio_exercises = len(workout_plan) - weight_training_exercises
    
    # If workout includes cardio, increase calorie burn
    if cardio_exercises > 0:
        cardio_ratio = cardio_exercises / len(workout_plan)
        calories_burned = calories_burned * (1 + (cardio_ratio * 0.5))
    
    return round(calories_burned)

def generate_workout_notes(workout_plan, rest_needs, user_id):
    """
    Generates helpful notes and tips for the workout.
    
    Args:
        workout_plan (list): The workout plan
        rest_needs (dict): Recovery status of muscle groups
        user_id (int): User ID for retrieving user data
        
    Returns:
        list: List of notes and tips
    """
    notes = []
    
    # Add basic workout notes
    notes.append("Remember to warm up properly before starting your workout.")
    notes.append("Stay hydrated throughout your session.")
    
    # Check if any exercises target muscle groups that need rest
    working_muscle_groups = set([ex["muscle_group"] for ex in workout_plan])
    
    muscles_needing_rest = [muscle for muscle in working_muscle_groups 
                           if muscle in rest_needs and rest_needs[muscle] == "needs_rest"]
    
    if muscles_needing_rest:
        notes.append(f"Be cautious with {', '.join(muscles_needing_rest)} exercises as these muscle groups may need more recovery.")
    
    # Check workout intensity
    intensity = calculate_intensity_level(workout_plan, "intermediate")
    
    if intensity == "intense" or intensity == "very intense":
        notes.append("This is a high-intensity workout. Listen to your body and adjust weights if needed.")
    
    # Add exercise-specific tips
    for exercise in workout_plan:
        if "Deadlift" in exercise["exercise"]:
            notes.append("Focus on proper form during deadlifts to protect your lower back.")
        elif "Squat" in exercise["exercise"]:
            notes.append("Keep your chest up and knees tracking over toes during squats.")
    
    # Add a motivational note
    motivational_phrases = [
        "Stay consistent - you're making progress!",
        "Every rep brings you closer to your goals.",
        "Focus on quality movements rather than just completing the workout."
    ]
    notes.append(random.choice(motivational_phrases))
    
    return notes

def create_default_workout(fitness_level="beginner"):
    """
    Creates a default workout when workout generation fails.
    
    Args:
        fitness_level (str): User's fitness level
        
    Returns:
        list: A basic default workout
    """
    if fitness_level == "beginner":
        return [
            {
                "exercise": "Bodyweight Squats",
                "sets": 3,
                "reps": "12-15",
                "rest": 60,
                "muscle_group": "legs"
            },
            {
                "exercise": "Push-ups",
                "sets": 3,
                "reps": "As many as possible",
                "rest": 60,
                "muscle_group": "chest"
            },
            {
                "exercise": "Walking Lunges",
                "sets": 2,
                "reps": "10 each leg",
                "rest": 60,
                "muscle_group": "legs"
            },
            {
                "exercise": "Plank",
                "sets": 3,
                "reps": "30 seconds",
                "rest": 45,
                "muscle_group": "core"
            },
            {
                "exercise": "Jumping Jacks",
                "sets": 3,
                "reps": "30 seconds",
                "rest": 30,
                "muscle_group": "cardio"
            }
        ]
    elif fitness_level == "intermediate":
        return [
            {
                "exercise": "Bodyweight Squats",
                "sets": 4,
                "reps": "15-20",
                "rest": 60,
                "muscle_group": "legs"
            },
            {
                "exercise": "Push-ups",
                "sets": 4,
                "reps": "10-15",
                "rest": 60,
                "muscle_group": "chest"
            },
            {
                "exercise": "Walking Lunges",
                "sets": 3,
                "reps": "12 each leg",
                "rest": 60,
                "muscle_group": "legs"
            },
            {
                "exercise": "Plank",
                "sets": 3,
                "reps": "45 seconds",
                "rest": 45,
                "muscle_group": "core"
            },
            {
                "exercise": "Mountain Climbers",
                "sets": 3,
                "reps": "45 seconds",
                "rest": 45,
                "muscle_group": "cardio"
            }
        ]
    else:  # advanced
        return [
            {
                "exercise": "Bodyweight Squats",
                "sets": 5,
                "reps": "20-25",
                "rest": 45,
                "muscle_group": "legs"
            },
            {
                "exercise": "Push-ups",
                "sets": 5,
                "reps": "15-20",
                "rest": 45,
                "muscle_group": "chest"
            },
            {
                "exercise": "Walking Lunges",
                "sets": 4,
                "reps": "15 each leg",
                "rest": 45,
                "muscle_group": "legs"
            },
            {
                "exercise": "Plank",
                "sets": 4,
                "reps": "60 seconds",
                "rest": 30,
                "muscle_group": "core"
            },
            {
                "exercise": "Burpees",
                "sets": 4,
                "reps": "45 seconds",
                "rest": 30,
                "muscle_group": "cardio"
            }
        ]


def evaluate_workout_effectiveness(user_id: int, days: int = 1) -> dict:
    """
    Evaluates how effective the user's most recent workout was.

    Args:
        user_id (int): The user's ID
        days (int): How many recent days of workouts to consider

    Returns:
        dict: Effectiveness score and supporting metrics
    """
    try:
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=days)).isoformat()
        end_date = today.isoformat()

        history = get_workout_history(user_id, startdate=start_date, enddate=end_date)

        if not history:
            return {
                "effectiveness_score": 50.0,
                "message": "No recent workout found.",
                "workout_summary": {}
            }

        # Evaluate the most recent workout
        recent = history[0]
        plan = recent.get("plan", [])  # Assume you store a serialized plan
        if not plan:
            return {
                "effectiveness_score": 50.0,
                "message": "No detailed workout plan found.",
                "workout_summary": {}
            }

        duration = estimate_duration(plan)
        intensity = calculate_intensity_level(plan, fitness_level="intermediate")

        # Map intensity to a numeric score
        intensity_map = {
            "none": 20,
            "light": 40,
            "moderate": 60,
            "intense": 80,
            "very intense": 100
        }
        score = intensity_map.get(intensity, 50)

        # Penalize if workout is too short (< 20 min)
        if duration < 20:
            score -= 10

        return {
            "effectiveness_score": round(np.clip(score, 0, 100), 1),
            "message": "Workout analyzed successfully.",
            "workout_summary": {
                "duration": duration,
                "intensity_label": intensity,
                "date": recent.get("workout_date"),
                "notes": recent.get("notes", "")
            }
        }

    except Exception as e:
        print(f"[ERROR] evaluate_workout_effectiveness: {e}")
        return {
            "effectiveness_score": 50.0,
            "message": "Error evaluating workout effectiveness.",
            "workout_summary": {}
        }
