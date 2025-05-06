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


def register_user(
    email, password_hash, name, gender, dob, height, weight, activity_level
):
    conn = None
    cursor = None

    try:
        conn = create_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                email, 
                password_hash, 
                name, 
                gender, 
                dateOfBirth, 
                height, 
                weight, 
                initialActivityLevel,
                
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (email, password_hash, name, gender, dob, height, weight, activity_level),
        )

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


def user_exists(email):
    cur = None
    conn = None

    try:
        conn = create_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, email, password_hash FROM users WHERE email = ?", (email,)
        )
        data = cur.fetchone()
        data = dict(data)
        if data:
            return dict(data)
        else:
            return False

    except Exception as e:
        return e

    finally:
        if cur:
            cur.close()
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
            "stress_level": stress,
            "energy_level": energy,
            "soreness_level": soreness,
        }

        cursor.execute(
            """
        INSERT INTO daily_checkins(
        user_id,
        weight,
        sleep_quality,
        stress_level,
        energy_level,
        soreness_level,
        check_in_date
         
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                user_input["weight"],
                user_input["sleep_quality"],
                user_input["stress_level"],
                user_input["energy_level"],
                user_input["soreness_level"],
                check_in_date,
            ),
        )

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
        datetime.datetime.strptime(date_string, "%d-%m-%Y")
        return True
    except ValueError:
        return False


######################################################### DO NOT KEEP BEYOND THIS ############
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
        cursor.execute(
            """
            UPDATE daily_checkins
            SET readiness_id = ?
            WHERE checkin_id = ?
        """,
            (readiness_id, checkin_id),
        )
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
    print(user_exists(1))
