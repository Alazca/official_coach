import sqlite3
import os
import datetime
from numpy import array, dot
from typing import Optional
from numpy.linalg import norm
from config.config import Config

# Database connection utility
def create_conn():
    """Create and return a database connection using configuration settings."""
    config = Config()
    db_path = config.get_database_path()
    # Connect to the database
    connection = sqlite3.connect(db_path)
    
    # Enable row factory to get named columns
    connection.row_factory = sqlite3.Row
    
    return connection

# Vector calculation functions
def normalize(data):
    """Normalize a vector using its norm."""
    return data / norm(data)

def weighted_similarity(user_vector, target_vector, factors):
    """Calculate weighted similarity between two vectors."""
    user_vector_weighted = user_vector * factors
    target_vector_weighted = target_vector * factors
    
    # Calculate cosine similarity with weighted vectors
    dot_product = dot(user_vector_weighted, target_vector_weighted)
    magnitude = norm(user_vector_weighted) * norm(target_vector_weighted)
    
    # Avoid division by zero
    if magnitude == 0:
        return 0
    
    return dot_product / magnitude

def evaluate_vectors(user_input: dict, user_id: Optional[int], factors: list = None) -> dict:
    """
    Evaluate a user's input vector against goal and overtraining vectors.
    
    Args:
        user_input: Dictionary containing user's current metrics
        user_id: The user's ID in the database
        factors: Optional weighting factors for vector components
    
    Returns:
        Dictionary with goal alignment, overtraining risk, and recommendation
    """
    # Default factors if none provided
    factors = array(factors or [1, 1, 1, 1, 1, 1, 1, 1])
    conn = None
    cursor = None
    
    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        # Get goal vector for user
        cursor.execute("""
            SELECT protein, calories, carbs, fats, sleep_quality, stress_level, soreness, readiness
            FROM user_goal_vectors
            WHERE user_id = ?
        """, (user_id,))
        goal_row = cursor.fetchone()
        
        # Get overtraining reference vector
        cursor.execute("""
            SELECT protein, calories, carbs, fats, sleep_quality, stress_level, soreness, readiness
            FROM overtraining_vector
            LIMIT 1
        """)
        overtraining_row = cursor.fetchone()
        
        if not goal_row:
            return {"error": f"No goal vector found for user {user_id}"}
        
        if not overtraining_row:
            return {"error": "Overtraining reference vector not defined in database."}
        
        # Convert to dictionaries
        goal_row = dict(goal_row)
        overtraining_row = dict(overtraining_row)
        
        # Create normalized vectors
        user_vector = normalize(array([
            user_input.get("protein", 0),
            user_input.get("calories", 0),
            user_input.get("carbs", 0),
            user_input.get("fats", 0),
            user_input.get("sleep_quality", 0),
            user_input.get("stress_level", 0),
            user_input.get("soreness", 0),
            user_input.get("readiness", 0)
        ]))
        
        goal_vector = normalize(array([
            goal_row["protein"],
            goal_row["calories"],
            goal_row["carbs"],
            goal_row["fats"],
            goal_row["sleep_quality"],
            goal_row["stress_level"],
            goal_row["soreness"],
            goal_row["readiness"]
        ]))
        
        overtraining_vector = normalize(array([
            overtraining_row["protein"],
            overtraining_row["calories"],
            overtraining_row["carbs"],
            overtraining_row["fats"],
            overtraining_row["sleep_quality"],
            overtraining_row["stress_level"],
            overtraining_row["soreness"],
            overtraining_row["readiness"]
        ]))
        
        # Calculate similarities
        goal_alignment = weighted_similarity(user_vector, goal_vector, factors)
        overtraining_risk = weighted_similarity(user_vector, overtraining_vector, factors)
        
        # Generate recommendation based on alignment and risk
        recommendation = generate_recommendation(goal_alignment, overtraining_risk)
        
        return {
            "goal_alignment": goal_alignment,
            "overtraining_risk": overtraining_risk,
            "recommendation": recommendation
        }
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_recommendation(goal_alignment, overtraining_risk):
    """Generate training recommendation based on alignment and risk scores."""
    # High alignment is good, high overtraining risk is bad
    if goal_alignment > 0.8:
        if overtraining_risk < 0.3:
            return "You're on track with your goals. Continue with your current regimen."
        elif overtraining_risk < 0.6:
            return "Good progress toward goals, but monitor for early signs of overtraining. Consider a light recovery day."
        else:
            return "While you're aligned with your goals, you're showing high risk of overtraining. Reduce intensity and focus on recovery."
    elif goal_alignment > 0.5:
        if overtraining_risk < 0.3:
            return "You're making progress toward your goals. Consider slightly increasing intensity."
        elif overtraining_risk < 0.6:
            return "Moderate progress toward goals. Maintain current intensity but improve recovery strategies."
        else:
            return "You're somewhat aligned with goals but showing signs of overtraining. Focus on nutrition and sleep quality."
    else:
        if overtraining_risk < 0.3:
            return "You're not aligned with your goals. Review your nutrition and training plan."
        elif overtraining_risk < 0.6:
            return "You're off track from goals and showing moderate stress. Consider consulting with your coach."
        else:
            return "You're off track and showing high stress markers. Take a recovery week and reassess your approach."

# User data functions from the original file
def user_exists(email):
    
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email,))
        data = cursor.fetchone()
        
        if data:
            return dict(data)
        return False
    except Exception as e:
        return e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_checkins(user_id, start_date=None, end_date=None):

    cursor = None
    conn = None
    
    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        if end_date and start_date:
            cursor.execute("""
                SELECT * FROM daily_checkins
                WHERE user_id = ? AND check_in_date BETWEEN ? AND ? 
                ORDER BY check_in_date DESC
                """, (user_id, start_date, end_date))
        else:
            cursor.execute("""
                SELECT * FROM daily_checkins
                WHERE user_id = ?
                ORDER BY check_in_date DESC
                """, (user_id,))

        data = cursor.fetchall()
        return [dict(row) for row in data]
    except Exception as e:
        return {"error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_workout_history(user_id=None, startdate=None, enddate=None):
    
    cursor = None
    conn = None
    
    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        if not user_id:
            return []
            
        params = [user_id]
        query = "SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = ?"
        
        if startdate and enddate:
            query += " AND workout_date >= ? AND workout_date <= ?"
            params.extend([startdate, enddate])
        elif startdate:
            query += " AND workout_date >= ?"
            params.append(startdate)
        elif enddate:
            query += " AND workout_date <= ?"
            params.append(enddate)
            
        query += " ORDER BY workout_date DESC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        return [dict(d) for d in data]
    except Exception as e:
        return {"error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def register_user(email, password_hash, name, gender, dob, height, weight, activity_level):
    
    conn = None
    cursor = None
    
    try:
        conn = create_conn()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (
                email, 
                password_hash, 
                name, 
                gender, 
                dateOfBirth, 
                height, 
                weight, 
                initialActivityLevel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email, password_hash, name, gender, dob, height, weight, activity_level))

        user_id = cursor.lastrowid
        conn.commit()
        
        # Initialize goal vector for new user
        initialize_user_goals(conn, user_id, activity_level)
        
        return int(user_id)
    except Exception as e:
        return str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def initialize_user_goals(conn, user_id, activity_level):
    """Initialize default goal vectors for a new user based on activity level."""
    cursor = conn.cursor()
    
    # Default values based on activity level
    if activity_level == 'low':
        protein = 1.2  # g/kg bodyweight
        calories = 2000
        carbs = 250    # g
        fats = 55      # g
    elif activity_level == 'moderate':
        protein = 1.6
        calories = 2400
        carbs = 300
        fats = 65
    else:  # high
        protein = 2.0
        calories = 2800
        carbs = 350
        fats = 75
    
    # Default metrics for all users
    sleep_quality = 8    # hours
    stress_level = 3     # 1-10 scale
    soreness = 3         # 1-10 scale
    readiness = 8        # 1-10 scale
    
    cursor.execute('''
        INSERT INTO user_goal_vectors (
            user_id, protein, calories, carbs, fats, 
            sleep_quality, stress_level, soreness, readiness
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, protein, calories, carbs, fats, 
          sleep_quality, stress_level, soreness, readiness))
    
    conn.commit()
    cursor.close()

def insert_check_in(user_id, weight, sleep, stress, energy, soreness, check_in_date):
    
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        # Calculate a basic readiness score
        readiness = calculate_readiness_score(sleep, stress, energy, soreness)
        
        cursor.execute("""
        INSERT INTO daily_checkins(
            user_id,
            weight,
            sleep_quality,
            stress_level,
            energy_level,
            soreness_level,
            readiness_score,
            check_in_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, weight, sleep, stress, energy, soreness, readiness, check_in_date))

        rowid = cursor.lastrowid
        conn.commit()
        
        # Get nutrition data for this user on this date
        nutrition_data = get_nutrition_data(conn, user_id, check_in_date)
        
        # Evaluate vector if nutrition data exists
        result = {}
        if nutrition_data:
            user_input = {
                "protein": nutrition_data.get("protein", 0),
                "calories": nutrition_data.get("calories", 0),
                "carbs": nutrition_data.get("carbs", 0),
                "fats": nutrition_data.get("fats", 0),
                "sleep_quality": sleep,
                "stress_level": stress,
                "energy_level": energy,
                "soreness": soreness
            }
            
            result = evaluate_vectors(user_input, user_id)
        
        return {
            "checkin_id": int(rowid),
            "readiness_score": readiness,
            "analysis": result
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_nutrition_data(conn, user_id, date):
    """Get nutrition data for a user on a specific date."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT protein, calories, carbs, fats 
        FROM nutrition_logs
        WHERE user_id = ? AND log_date = ?
    """, (user_id, date))
    
    data = cursor.fetchone()
    cursor.close()
    
    if data:
        return dict(data)
    return None

def calculate_readiness_score(sleep, stress, energy, soreness):
    """Calculate a readiness score based on user metrics."""
    # Convert all inputs to 0-10 scale if they aren't already
    sleep_score = min(10, sleep * 1.25)  # Assuming sleep is in hours, max good sleep = 8h
    
    # Invert stress and soreness (lower is better)
    stress_inverted = 10 - stress
    soreness_inverted = 10 - soreness
    
    # Calculate weighted average
    weights = [0.3, 0.2, 0.3, 0.2]  # sleep, stress, energy, soreness
    weighted_score = (
        sleep_score * weights[0] + 
        stress_inverted * weights[1] + 
        energy * weights[2] + 
        soreness_inverted * weights[3]
    )
    
    # Round to one decimal place
    return round(weighted_score, 1)

def validate_date(date_string):
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    # Example usage
    user_input = {
        "protein": 120,
        "calories": 2200,
        "carbs": 250,
        "fats": 60,
        "sleep_quality": 7,
        "stress_level": 4,
        "soreness": 3,
        "readiness": 8
    }
    
    result = evaluate_vectors(user_input, 3)
    print(result)
