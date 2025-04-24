CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    dateOfBirth DATE,
    height REAL,
    weight REAL,
    initialActivityLevel TEXT CHECK(initialActivityLevel IN ('Sedentary', 'Casual', 'Moderate', 'Active', 'Intense')),
    currentActivityLevel TEXT CHECK(currentActivityLevel IN ('Sedentary', 'Casual', 'Moderate', 'Active', 'Intense')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_checkins (
    checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    weight REAL,
    sleep_quality INTEGER,
    stress_level INTEGER,
    energy_level INTEGER,
    soreness_level INTEGER,
    readiness_id INTEGER,
    check_in_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    goalType TEXT CHECK(goalType IN ('Strength', 'Endurance', 'Weight-Loss', 'Performace')),
    description TEXT,
    target_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE workouts (
    workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    workout_date TEXT,
    workout_type TEXT CHECK(workout_type IN ('Strength', 'Cardio', 'Mobility', 'Recovery')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE exercises (
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
    FOREIGN KEY (workout_id) REFERENCES workouts(workout_id),
    FOREIGN KEY (exercise_id) REFERENCES Exercises(exercise_id)
);

CREATE TABLE progress_Log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    log_date TEXT,
    logged_weight INTEGER,
    BMI REAL CHECK (BMI >= 0),
    notes TEXT
);

CREATE TABLE readiness_scores (
    readiness_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    readiness_level INTEGER CHECK(readiness_score BETWEEN 0 AND 100),
    contributing_factors TEXT, 
    readiness_date DATE NOT NULL,
    source TEXT CHECK(source IN ('Manual', 'Auto', 'Coach')),
    alignment_score REAL,
    overtraining_score REAL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE fitness_analyses (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_date DATE NOT NULL,
    strength_score REAL,
    conditioning_score REAL,
    overall_score REAL,
    fitness_level TEXT,
    analysis_data TEXT, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE workout_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    duration_weeks INTEGER NOT NULL,
    sessions_per_week INTEGER NOT NULL,
    strength_ratio REAL NOT NULL,
    conditioning_ratio REAL NOT NULL,
    created_at TIMESTAMP,
    plan_data TEXT,
    active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE target_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dimensions TEXT NOT NULL, 
    vector TEXT NOT NULL  
)
