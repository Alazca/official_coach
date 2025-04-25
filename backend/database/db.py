import sqlite3
from typing import Optional, List, Tuple
from backend.config.config import Config
import datetime

def create_conn():
    con = Config()
    db_path = con.get_database_path()
    # Connect to the database
    connection = sqlite3.connect(db_path)

    # Optional: Enable row factory to get named columns
    connection.row_factory = sqlite3.Row

    return connection

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
        
        if user_id is None:
            raise ValueError("No User ID found!")

        return user_id

    except Exception as e:
        error_message = str(e)
        return error_message
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def insert_check_in(user_id, weight, sleep, stress, energy, soreness, check_in_date):
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()

        user_input = {
        "weight": weight,
        "sleep_quality": sleep,
        "stress_level" : stress,
        "energy_level" : energy,
        "soreness_level": soreness
        }
        
        cursor.execute("""
        INSERT INTO daily_checkins(
        user_id,
        weight,
        sleep_quality,
        stress_level,
        energy_level,
        soreness_level,
        check_in_date
         
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, 
            user_input["weight"], 
            user_input["sleep_quality"], 
            user_input["stress_level"], 
            user_input["energy_level"], 
            user_input["soreness_level"], 
            check_in_date
        ))

        rowid = cursor.lastrowid
        conn.commit()
        
        if rowid is None:
            raise ValueError("No ID found!")

        return rowid

    except Exception as e:
        return str(e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def validate_date(date_string):

    try:
        datetime.datetime.strptime(date_string, '%d-%m-%Y')
        return True
    except ValueError:
        return False


def user_exists(email):
    cur = None
    conn = None
    
    try:
        conn = create_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, email, password_hash FROM users WHERE email = ?", (email,))
        data = cur.fetchone()
        if data:  # Only call dict() if data exists
            return dict(data)
        else:
            return False  # clean False, not Exception
    except Exception as e:
        return e
    finally:
        if cur:
            cur.close()
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
                """, (user_id,))

        data = cursor.fetchall()
        data = [dict(row) for row in data]
        return data
    
    except Exception as e:
        print(f"Error: Get all Checkins Failed due to {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_workout_history(user_id: int, 
                        time_frame: Optional[str] = None, 
                        startdate: Optional[str] = None, 
                        enddate: Optional[str] = None) -> List[dict]:
    """
    Retrieves workout history for a user using a time frame or explicit date range.

    Args:
        user_id (int): The user's ID
        time_frame (str, optional): 'week', 'month', 'quarter', or 'year'
        startdate (str, optional): Start date in 'YYYY-MM-DD'
        enddate (str, optional): End date in 'YYYY-MM-DD'

    Returns:
        list of dict: Workout records
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()

        if not user_id:
            return []

        # If no explicit dates, calculate startdate using time_frame
        if not startdate:
            today = datetime.date.today()
            if time_frame == "week":
                # Convert datetime.date object to string format
                startdate = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            elif time_frame == "month":
                # Handle month calculation more accurately
                # Get the first day of current month
                first_day_current_month = today.replace(day=1)
                
                # Calculate first day of previous month
                if today.month == 1:  # January
                    previous_month = first_day_current_month.replace(year=today.year - 1, month=12)
                else:
                    previous_month = first_day_current_month.replace(month=today.month - 1)
                
                startdate = previous_month.strftime('%Y-%m-%d')
            elif time_frame == "quarter":
                # Calculate date 3 months ago
                month = today.month - 3
                year = today.year
                if month <= 0:  # Handle year boundary
                    month += 12
                    year -= 1
                
                # Handle potential day-of-month issues (e.g., Feb 30 doesn't exist)
                try:
                    quarter_date = today.replace(year=year, month=month)
                except ValueError:
                    # If day doesn't exist in the target month, use the last day of that month
                    if month == 2:  # February
                        last_day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
                    elif month in [4, 6, 9, 11]:  # April, June, September, November
                        last_day = 30
                    else:
                        last_day = 31
                    quarter_date = today.replace(year=year, month=month, day=last_day)
                
                startdate = quarter_date.strftime('%Y-%m-%d')
            elif time_frame == "year":
                # Handle leap year correctly
                try:
                    year_ago = today.replace(year=today.year - 1)
                except ValueError:
                    # Handle February 29 in leap years
                    if today.month == 2 and today.day == 29:
                        year_ago = datetime.date(today.year - 1, 2, 28)
                    else:
                        raise
                
                startdate = year_ago.strftime('%Y-%m-%d')
            else:
                startdate = None  # allow full history if no time_frame
        
        # Set enddate to today if not specified
        if not enddate:
            enddate = datetime.date.today().strftime('%Y-%m-%d')

        # Build dynamic query
        query = "SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = ?"
        params = [user_id]

        if startdate:
            query += " AND workout_date >= ?"
            params.append(startdate)
        if enddate:
            query += " AND workout_date <= ?"
            params.append(enddate)

        query += " ORDER BY workout_date DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        print(f"Error in get_workout_history: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_nutrition_history(user_id, start_date=None, end_date=None):
    """
    Retrieve nutrition history for a user from the nutrition_logs table.
    Returns data grouped by date with totals for calories, protein, carbs, and fats.
    """
    cursor = None
    conn = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        # Query to get daily nutrition totals from the nutrition_logs table
        query = """
        SELECT 
            log_date, 
            SUM(calories) as total_calories,
            SUM(protein) as total_protein,
            SUM(carbs) as total_carbs,
            SUM(fats) as total_fats
        FROM nutrition_logs
        WHERE user_id = ?
        """
        
        params = [user_id]
        
        if start_date and end_date:
            query += " AND log_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND log_date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND log_date <= ?"
            params.append(end_date)
            
        query += " GROUP BY log_date ORDER BY log_date"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        if not data:
            # If no data found, return empty list instead of sample data
            return []
            
        return [dict(row) for row in data]
    except Exception as e:
        print(f"Error fetching nutrition history: {str(e)}")
        return str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_weight_history(user_id, start_date=None, end_date=None):
    """
    Retrieve weight history from daily_checkins and/or Progress_Log tables
    """
    cursor = None
    conn = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        # Using daily_checkins table since it already has weight data
        query = """
        SELECT check_in_date as date, weight
        FROM daily_checkins
        WHERE user_id = ?
        """
        
        params = [user_id]
        
        if start_date and end_date:
            query += " AND check_in_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND check_in_date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND check_in_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY check_in_date"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        return [dict(row) for row in data]
    except Exception as e:
        return str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_exercise_distribution(user_id, start_date=None, end_date=None):
    """
    Get distribution of exercises by category or type
    """
    cursor = None
    conn = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        
        # Query to get workout types count
        query = """
        SELECT workout_type, COUNT(*) as count
        FROM workouts
        WHERE user_id = ?
        """
        
        params = [user_id]
        
        if start_date and end_date:
            query += " AND workout_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND workout_date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND workout_date <= ?"
            params.append(end_date)
            
        query += " GROUP BY workout_type"
        
        cursor.execute(query, params)
        workout_types = cursor.fetchall()
        workout_types = [dict(row) for row in workout_types]
        
        # Query to get exercise categories count
        # This is more complex as it requires joining with the workout_sets table
        exercise_category_query = """
        SELECT e.category, COUNT(*) as count
        FROM workout_sets ws
        JOIN Exercises e ON ws.exercise_id = e.exercise_id
        JOIN workouts w ON ws.workout_id = w.workout_id
        WHERE w.user_id = ?
        """
        
        params = [user_id]
        
        if start_date and end_date:
            exercise_category_query += " AND w.workout_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            exercise_category_query += " AND w.workout_date >= ?"
            params.append(start_date)
        elif end_date:
            exercise_category_query += " AND w.workout_date <= ?"
            params.append(end_date)
            
        exercise_category_query += " GROUP BY e.category"
        
        cursor.execute(exercise_category_query, params)
        exercise_categories = cursor.fetchall()
        exercise_categories = [dict(row) for row in exercise_categories]
        
        # Query to get muscle groups count
        muscle_group_query = """
        SELECT e.muscle_group, COUNT(*) as count
        FROM workout_sets ws
        JOIN Exercises e ON ws.exercise_id = e.exercise_id
        JOIN workouts w ON ws.workout_id = w.workout_id
        WHERE w.user_id = ?
        """
        
        params = [user_id]
        
        if start_date and end_date:
            muscle_group_query += " AND w.workout_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            muscle_group_query += " AND w.workout_date >= ?"
            params.append(start_date)
        elif end_date:
            muscle_group_query += " AND w.workout_date <= ?"
            params.append(end_date)
            
        muscle_group_query += " GROUP BY e.muscle_group"
        
        cursor.execute(muscle_group_query, params)
        muscle_groups = cursor.fetchall()
        muscle_groups = [dict(row) for row in muscle_groups]
        
        return {
            "workout_types": workout_types,
            "exercise_categories": exercise_categories,
            "muscle_groups": muscle_groups
        }
    
    except Exception as e:
        return str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_target_profile(user_id, start_date=None, end_date=None) -> Tuple[List[str], List[float]]:
    """
    Get the user's target profile for use.
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()

        # Query to get target profile dimensions and vector
        query = """
        SELECT dimensions, vector
        FROM target_profiles
        WHERE user_id = ?
        """

        params = [user_id]

        if start_date and end_date:
            query += " AND created_at BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND created_at <= ?"
            params.append(end_date)

        # Order by latest first in case of multiple entries
        query += " ORDER BY created_at DESC LIMIT 1"

        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return [], []
        
        # Parse the dimensions from the database
        dimensions = row["dimensions"].split(",")
        vector = row["vector"].split(",")
        
        vector = [float(val) for val in vector]
        
        return dimensions,vector
    
    except Exception as e:
        print(f"[ERROR] get_target_profile failed: {e}")
        return [], []  
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_latest_checkin(user_id: int) -> Optional[int]:
    """
    Get the latest check-in ID for a specific user.
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checkin_id
            FROM daily_checkins
            WHERE user_id = ?
            ORDER BY check_in_date DESC, created_at DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        return row["checkin_id"] if row else None

    except Exception as e:
        print(f"Error in get_latest_checkin_id: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_readiness_score(data: dict) -> Optional[int]:
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO readiness_scores (
                user_id, readiness_score, contributing_factors,
                readiness_date, source, alignment_score, overtraining_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["user_id"], data["readiness_score"], data["contributing_factors"],
            data["readiness_date"], data["source"],
            data.get("alignment_score"), data.get("overtraining_score")
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"save_readiness_score failed: {e}")
        return None
    finally:
        if cursor: 
            cursor.close()
        if conn: 
            conn.close()

def save_fitness_analysis(data: dict) -> Optional[int]:
    """
    Save a fitness analysis record.
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fitness_analyses (
                user_id,
                analysis_date,
                strength_score,
                conditioning_score,
                overall_score,
                fitness_level,
                analysis_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["user_id"],
            data["analysis_date"],
            data["strength_score"],
            data["conditioning_score"],
            data["overall_score"],
            data["fitness_level"],
            str(data["analysis_data"])
        ))

        conn.commit()
        return cursor.lastrowid

    except Exception as e:
        print(f"save_fitness_analysis failed: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_active_workout_plan(user_id: int) -> dict:
    """
    Get the user's active workout plan.
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM workout_plans
            WHERE user_id = ? AND active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        return dict(row) if row else {}

    except Exception as e:
        print(f"get_active_workout_plan failed: {e}")
        return {}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_goals(user_id: int) -> list:
    """
    Retrieve all goals for a user.
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM goals
            WHERE user_id = ?
            ORDER BY target_date
        """, (user_id,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        print(f"get_user_goals failed: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_progress_logs(user_id: int, start_date=None, end_date=None) -> list:
    """
    Get progress logs (weight + BMI) for a user.
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM progress_log
            WHERE user_id = ?
        """
        params = [user_id]

        if start_date and end_date:
            query += " AND log_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND log_date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND log_date <= ?"
            params.append(end_date)

        query += " ORDER BY log_date"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        print(f"get_progress_logs failed: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_baseline(user_id):
    """
    Retrieves user's baseline metrics from database.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        dict: Dictionary of baseline metrics
    """
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()

        query = """
        SELECT sleep_quality, stree_level, energy_level, sorenss
        FROM daily_checkins
        WHERE user_id = ?
        """
        cursor.execute(query, (user_id))
        row = cursor.fetchone()

        if row:
            return {
                "sleep_quality": row["sleep_quality"],
                "stress_level": row["stress_level"],
                "energy_level": row["energy_level"],
                "soreness_level": row["soreness_level"],
            }
        else:
            # Defaults 
            return {
                "sleep_quality": 8.0,
                "stress_level": 5.0,
                "energy_level": 5.0,
                "soreness_level": 2.0,
            }
        
    except Exception as e:
        print(f"Error in get_user_baseline: {str(e)}")
        return {}


def update_checkin_with_readiness(checkin_id: int, readiness_id: int) -> bool:
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE daily_checkins
            SET readiness_id = ?
            WHERE checkin_id = ?
        """, (readiness_id, checkin_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Failed to update readiness_id: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print(get_all_checkins(3, start_date='2025-04-03', end_date='2025-04-08'))
