import sqlite3
import os
from backend.config.config import Config

def check_database():
    config = Config()
    db_path = config.get_database_path()
    print(f"Attempting to connect to database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database file does not exist at: {db_path}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute("SELECT email, name, created_at FROM users")
        users = cursor.fetchall()
        print("\nUsers in database:")
        for user in users:
            print(f"Email: {user[0]}, Name: {user[1]}, Created: {user[2]}")
            
        # Check goals table
        cursor.execute("SELECT goal_id, goal_type, status FROM goals")
        goals = cursor.fetchall()
        print("\nGoals in database:")
        for goal in goals:
            print(f"Goal ID: {goal[0]}, Type: {goal[1]}, Status: {goal[2]}")
            
    except Exception as e:
        print(f"Error accessing database: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database() 