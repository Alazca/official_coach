
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    dateOfBirth DATE,
    height REAL,
    weight REAL,
    initialActivityLevel TEXT CHECK(initialActivityLevel IN ('Sedentary', 'Casual', 'Moderate', 'Active', 'Intense')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    weight REAL,
    sleep_quality INTEGER,
    stress_level INTEGER,
    energy_level INTEGER,
    soreness_level INTEGER,
    readiness_score INTEGER NULL,
    check_in_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE Goals (
    goalId INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    goalType TEXT CHECK(goalType IN ('Strength', 'Endurance', 'Weight-Loss', 'Performace')),
    description TEXT,
    target_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    workout_date TEXT,
    workout_type TEXT CHECK(workout_type IN ('Strength', 'Cardio', 'Mobility', 'Recovery')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE Exercises (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT CHECK(category IN ('Compound', 'Isolation', 'Cardio', 'Mobility', 'Olympic-Style')),
    muscle_group TEXT,
    difficulty TEXT CHECK(difficulty IN ('Beginner', 'Intermediate', 'Advanced', 'Professional'))
);

CREATE TABLE workout_sets (
    workout_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER,
    exercise_id INTEGER,
    lifting_weight REAL,
    sets INTEGER,
    reps INTEGER,
    duration INTEGER,
    rest_per_set INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES Exercises(exercise_id)
);

CREATE TABLE Progress_Log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    log_date TEXT,
    logged_weight INTEGER,
    BMI REAL CHECK (BMI >= 0),
    notes TEXT,
);
