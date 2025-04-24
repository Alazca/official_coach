from backend.database.db import create_conn

def get_user_baseline(user_id):
    """
    Retrieves user's baseline metrics from database.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        dict: Dictionary of baseline metrics
    """
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


