import sqlite3
from config import Config
import datetime

def create_conn():
    con = Config()
    db_path = con.get_database_path()
    # Connect to the database
    connection = sqlite3.connect(db_path)

    # Optional: Enable row factory to get named columns
    connection.row_factory = sqlite3.Row

    return connection


def user_exists(email):
    try:
        conn = create_conn()
        cur = conn.cursor()
        cur.execute(f"""SELECT id, email, password_hash FROM users WHERE email = '{email}'""")
        data = cur.fetchone()
        data = dict(data)
        if data:
            return data
        if not data:
            return False
    except Exception as e:
        return e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_all_checkins(user_id, start_date=None, end_date=None):
    try:
        connection = create_conn()
        cursor = connection.cursor()
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
        return e  # Consider returning a message instead of the exception object
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
            cursor.execute("""
            SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = ?
             AND workout_date >= ? AND workout_date <= ?""", (user_id, startdate, enddate))
        elif startdate:
            cursor.execute("""
                        SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = ?
                         AND workout_date >= ? """, (user_id, startdate))
        elif enddate:
            cursor.execute("""
                        SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = ? AND
                         workout_date <= ?""", (user_id, enddate))
        else:
            cursor.execute(f"""
                    SELECT workout_type, workout_date, notes FROM workouts WHERE user_id = {user_id}""")

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

def validate_date(date_string):

    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    print(get_all_checkins(3, start_date='2025-04-03', end_date='2025-04-08'))
