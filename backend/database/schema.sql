CREATE DATABASE IF NOT EXISTS coach_db;
USE coach_db;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    gender ENUM('Male', 'Female', 'Other'),
    dateOfBirth DATE,
    height DECIMAL(5,2),
    weight DECIMAL(5,2),
    initialActivityLevel ENUM('Sedentary', 'Casual', 'Moderate', 'Active', 'Intense'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE daily_checkins (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    weight DECIMAL(5,2),
    sleep_quality INT,
    stress_level INT,
    energy_level INT,
    soreness_level INT,
    readiness_score INT,
    check_in_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE Table Goals(
    goalId INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    goalType ENUM('Strength', 'Endurance', 'Weight-Loss', 'Performace'),
    description TEXT,
    target_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE workouts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    workout_date DATE,
    workout_type ENUM('Strength', 'Cardio', 'Mobility', 'Recovery'),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Exercises (
    exercise_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    category ENUM('Compound', 'Isolation', 'Cardio', 'Mobility', 'Olympic-Style'),
    muscle_group VARCHAR(50),
    difficulty ENUM('Beginner', 'Intermediate', 'Advanced', 'Professional')
);

CREATE TABLE workout_sets (
    workout_exercise_id INT PRIMARY KEY AUTO_INCREMENT,
    workout_id INT,
    exercise_id INT,
    lifting_weight DECIMAL(6,2),
    sets INT,
    reps INT,
    duration INT,
    rest_per_set INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workout_id) REFERENCES workouts(id),
    FOREIGN KEY (exercise_id) REFERENCES Exercises(exercise_id)
);

CREATE TABLE Progress_Log(
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    log_date DATE,
    logged_weight INT,
    BMI DECIMAL(5,2) CHECK CHECK (body_fat_percentage >= 0 AND body_fat_percentage <= 100),
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE meals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    meal_date DATE,
    meal_name VARCHAR(100),
    calories INT,
    protein DECIMAL(6,2),
    carbs DECIMAL(6,2),
    fats DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE AI_Feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    workout_id INT,
    feedback_text TEXT,
    score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (workout_id) REFERENCES Workouts(workout_id)
);

