import sqlite3
import re
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
jdbc_url = f"jdbc:sqlite:{os.path.join(base_dir, '../database/coach.db')}"

def create_conn():
    # The pattern matches everything after "jdbc:sqlite:"
    match = re.match(r'jdbc:sqlite:(.*)', jdbc_url)

    if not match:
        raise ValueError("Invalid SQLite JDBC URL format")

    db_path = match.group(1)

    # Connect to the database
    connection = sqlite3.connect(db_path)

    # Optional: Enable row factory to get named columns
    connection.row_factory = sqlite3.Row

    return connection


def get_all_checkins(user_id, date):

    try:
        connection = create_conn()
        cursor = connection.cursor()
        if date:
            cursor.execute(f"""SELECT * FROM daily_checkins
            WHERE user_id = {user_id} AND check_in_date = '{date}' 
            ORDER BY check_in_date DESC""")
            data = cursor.fetchall()
            data = [dict(row) for row in data]
            print(data)
            return data
        else:
            cursor.execute(f"""SELECT * FROM daily_checkin
            WHERE user_id = {user_id}""")
            data = cursor.fetchall()
            data = [dict(row) for row in data]
            print(data)
            return data
    except Exception as e:
        print(f"Error {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

#still have to test
def get_workout_history(user_id=None, startdate=None, enddate=None):

    try:
        connection = create_conn()
        cursor = connection.cursor()
        if not user_id:
            return []
        if startdate and enddate:
            cursor.execute(f"""
            SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = {user_id}
             AND workout_date >= '{startdate}' AND workout_date <= '{enddate}'""")
        elif startdate:
            cursor.execute(f"""
                        SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = {user_id}
                         AND workout_date >= '{startdate}' """)
        elif enddate:
            cursor.execute(f"""
                        SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = {user_id}
                         AND workout_date >= '{startdate}' AND workout_date <= '{enddate}'""")

        data = cursor.fetchall()
        data = [dict(d) for d in data]
        return data
    except Exception as e:
        return str(e)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def register_user(email, password_hash, name, gender, dob, height, weight, activity_level):
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

        return int(user_id)
    except Exception as e:
        error_message = str(e)
        return error_message
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def insert_check_in(user_id, weight, sleep, stress, energy, soreness, check_in_date):
    try:
        conn = create_conn()
        cursor = conn.cursor()
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
        """, (user_id, weight, sleep, stress, energy, soreness, None, check_in_date))

        rowid = cursor.lastrowid
        conn.commit()
        return int(rowid)
    except Exception as e:
        return str(e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    get_all_checkins(1, "2025-04-02")
