from backend.config.config import Config

def get_user_baseline(user_id):
    """
    Retrieves user's baseline metrics from database.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        dict: Dictionary of baseline metrics
    """
    try:
        conn = Config().get_connection()
        cursor = conn.cursor()
        
        # This would typically query the user's baseline data from the database
        # For now, return default values
        baseline = {
            "baseline_weight": 70,
            "baseline_sleep": 7,
            "baseline_stress": 5,
            "baseline_energy": 7,
        }
        
        return baseline
        
    except Exception as e:
        print(f"Error in get_user_baseline: {str(e)}")
        return {}