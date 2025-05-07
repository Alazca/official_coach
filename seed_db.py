#!/usr/bin/env python3
import os
import sqlite3
import random
import datetime
import uuid

from backend.config.config import Config

DB_PATH = Config().get_database_path()


# ——— HELPERS ———
def create_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def insert_goal(conn, user_goal):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO goals (user_id, goal_type, category, description, status)
        VALUES (?, ?, ?, ?, ?)
    """,
        (None, user_goal, "Strength", f"Auto-gen goal: {user_goal}", "In Progress"),
    )
    return cur.lastrowid


def insert_user(
    conn,
    email,
    pwd_hash,
    name,
    gender,
    dob,
    height,
    weight,
    ia_level,
    ca_level,
    goal_id,
):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE goals SET user_id = ? WHERE goal_id = ?
    """,
        (None, goal_id),
    )
    cur.execute(
        """
        INSERT INTO users
          (email, password_hash, name, gender, dateOfBirth, height, weight,
           initialActivityLevel, currentActivityLevel, goal_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            email,
            pwd_hash,
            name,
            gender,
            dob,
            height,
            weight,
            ia_level,
            ca_level,
            goal_id,
        ),
    )
    return cur.lastrowid


def insert_checkin(conn, user_id, date, weight):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO daily_checkins
          (user_id, weight, sleep_quality, stress_level, energy_level, soreness_level, check_in_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            weight,
            random.randint(6, 9),  # sleep_quality
            random.randint(1, 5),  # stress_level
            random.randint(2, 8),  # energy_level
            random.randint(0, 4),  # soreness_level
            date.strftime("%Y-%m-%d"),
        ),
    )
    return cur.lastrowid


def insert_nutrition(conn, user_id, date):
    cur = conn.cursor()
    cal = random.randint(1800, 3000)
    protein = random.uniform(60, 160)
    carbs = random.uniform(100, 400)
    fats = random.uniform(50, 110)
    fiber = random.uniform(15, 40)
    hydration = random.uniform(1.5, 3.5)
    sim_score = round(random.uniform(0.5, 1.0), 3)
    cur.execute(
        """
        INSERT INTO nutrition_log
          (user_id, calories, protein, carbs, fats, fiber, hydration, similarity_score, log_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            cal,
            protein,
            carbs,
            fats,
            fiber,
            hydration,
            sim_score,
            date.strftime("%Y-%m-%d"),
        ),
    )
    return cur.lastrowid


def insert_workout(conn, user_id, date):
    types = ["Strength", "Cardio", "Mobility", "Recovery"]
    w_type = random.choice(types)
    notes = f"Auto-gen {w_type} session"
    duration = random.randint(20, 75)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO workouts (user_id, workout_date, workout_type, notes, duration)
        VALUES (?, ?, ?, ?, ?)
    """,
        (user_id, date.strftime("%Y-%m-%d"), w_type, notes, duration),
    )
    return cur.lastrowid


def insert_workout_sets(conn, workout_id):
    cur = conn.cursor()
    num_exercises = random.randint(2, 4)
    for _ in range(num_exercises):
        exercise_id = random.randint(
            1, 10
        )  # assumes you have at least 10 exercises seeded
        sets = random.randint(2, 5)
        reps = random.randint(5, 12)
        weight = round(random.uniform(20, 150), 1)
        is_rm = 1 if random.random() < 0.05 else 0
        cur.execute(
            """
            INSERT INTO workout_sets
              (workout_id, exercise_id, lifting_weight, sets, reps, is_one_rm)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (workout_id, exercise_id, weight, sets, reps, is_rm),
        )


# ——— MAIN SCRIPT ———
def main():
    conn = create_conn()
    try:
        # 1) Random user & goal
        goal_type = random.choice(
            ["Strength", "Endurance", "Weight-Loss", "Performance"]
        )
        goal_id = insert_goal(conn, goal_type)

        email = f"Test@example.com"
        pwd_hash = "scrypt:32768:8:1$wGM0ZETGcN2qUCkw$f79629590d0d3eef8e87d22b66d7bf4aec18402ab3ffcc01242bac3dcb78e8602b441550d7b97cf5312e5c23aa6205386c2d9dc7930ba1ac51b88cc6eff9c900"
        name = f"TestUser{random.randint(1000,9999)}"
        gender = random.choice(["Male", "Female", "Other"])
        dob = (
            datetime.date.today()
            - datetime.timedelta(days=random.randint(18 * 365, 60 * 365))
        ).isoformat()
        height = round(random.uniform(160, 190), 1)
        weight0 = round(random.uniform(60, 90), 1)
        ia_level = random.choice(
            ["Sedentary", "Casual", "Moderate", "Active", "Intense"]
        )
        ca_level = ia_level

        user_id = insert_user(
            conn,
            email,
            pwd_hash,
            name,
            gender,
            dob,
            height,
            weight0,
            ia_level,
            ca_level,
            goal_id,
        )
        print(f"Created user {user_id} ({email}) with goal {goal_type}")

        # 2) One year of daily data
        today = datetime.date.today()
        start = today - datetime.timedelta(days=365)
        current_weight = weight0

        for i in range(366):
            day = start + datetime.timedelta(days=i)
            # simulate small weight drift
            current_weight += random.uniform(-0.1, 0.1)
            insert_checkin(conn, user_id, day, round(current_weight, 1))
            insert_nutrition(conn, user_id, day)

            # ~3 workouts/week
            if random.random() < 3 / 7:
                w_id = insert_workout(conn, user_id, day)
                insert_workout_sets(conn, w_id)

        conn.commit()
        print("Injected 1 year of check-ins, nutrition logs, and workouts.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
