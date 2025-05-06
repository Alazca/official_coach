CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT,
  gender TEXT CHECK (gender IN ('Male', 'Female', 'Other')),
  dateOfBirth DATE,
  height REAL,
  weight REAL,
  initialActivityLevel TEXT CHECK (
    initialActivityLevel IN (
      'Sedentary',
      'Casual',
      'Moderate',
      'Active',
      'Intense'
    )
  ),
  currentActivityLevel TEXT CHECK (
    currentActivityLevel IN (
      'Sedentary',
      'Casual',
      'Moderate',
      'Active',
      'Intense'
    )
  ),
  goal_id INTEGER NOT NUlL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_profile (
  profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_id INTEGER,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  dimensions TEXT NOT NULL,
  vector TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id),
  FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
);

CREATE TABLE IF NOT EXISTS daily_checkins (
  checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  readiness_id INTEGER,
  weight REAL,
  sleep_quality INTEGER,
  stress_level INTEGER,
  energy_level INTEGER,
  soreness_level INTEGER,
  check_in_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS workouts (
  workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  workout_date DATE,
  workout_type TEXT CHECK (
    workout_type IN ('Strength', 'Cardio', 'Mobility', 'Recovery')
  ),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS workout_sets (
  workout_exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
  workout_id INTEGER NOT NULL,
  exercise_id INTEGER NOT NULL,
  lifting_weight REAL NOT NULL,
  sets INTEGER NOT NULL,
  reps INTEGER NOT NULL,
  duration INTEGER,
  rest_per_set INTEGER,
  is_one_rm INTEGER NOT NULL DEFAULT 0 CHECK (is_one_rm IN (0, 1)),
  rm_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (workout_id) REFERENCES workouts (workout_id),
  FOREIGN KEY (exercise_id) REFERENCES exercises (exercise_id)
);

--- This is to show how able the user is 
CREATE TABLE IF NOT EXISTS readiness_scores (
  readiness_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  readiness_level INTEGER CHECK (readiness_level BETWEEN 0 AND 100),
  contributing_factors TEXT,
  readiness_date DATE NOT NULL,
  source TEXT CHECK (source IN ('Manual', 'Auto', 'Coach')),
  alignment_score REAL,
  overtraining_score REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS goals (
  goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  goal_type TEXT CHECK (
    goal_type IN (
      'Strength',
      'Endurance',
      'Weight-Loss',
      'Performance',
      'Default'
    )
  ),
  category TEXT CHECK (
    category IN (
      'Nutrition',
      'Strength',
      'Conditioning',
      'Recovery'
    )
  ) NOT NULL,
  description TEXT,
  target_value REAL,
  unit TEXT,
  target_date TEXT,
  status TEXT CHECK (
    status IN (
      'Not Started',
      'In Progress',
      'Completed',
      'Abandoned'
    )
  ) DEFAULT 'Not Started',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS goal_templates (
  template_id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_type TEXT,
  category TEXT,
  name TEXT,
  description TEXT,
  recommended_duration INTEGER,
  difficulty_level TEXT CHECK (
    difficulty_level IN (
      'Beginner',
      'Intermediate',
      'Advanced',
      'Professional'
    )
  ),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goal_progress (
  progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
  goal_id INTEGER,
  current_value REAL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
);

-- CREATE TABLE goal_exercises (
--   goal_id INTEGER,
--   exercise_id INTEGER,
--   target_weight REAL,
--   target_reps INTEGER,
--   target_sets INTEGER,
--   PRIMARY KEY (goal_id, exercise_id),
--   FOREIGN KEY (goal_id) REFERENCES goals (goal_id),
--   FOREIGN KEY (exercise_id) REFERENCES exercises (exercise_id)
-- );
CREATE TABLE IF NOT EXISTS goal_nutrition (
  goal_id INTEGER,
  target_calories REAL,
  target_protein REAL,
  target_carbs REAL,
  target_fats REAL,
  target_fiber REAL,
  target_hydration REAL,
  PRIMARY KEY (goal_id),
  FOREIGN KEY (goal_id) REFERENCES goals (goal_id)
);

CREATE TABLE IF NOT EXISTS goal_recommendations (
  recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  goal_type TEXT,
  category TEXT,
  description TEXT,
  reason TEXT,
  recommendation_score REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS exercises (
  exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  category TEXT CHECK (
    category IN (
      'Compound',
      'Isolation',
      'Cardio',
      'Mobility',
      'Olympic-Style'
    )
  ),
  muscle_group TEXT,
  difficulty TEXT CHECK (
    difficulty IN (
      'Beginner',
      'Intermediate',
      'Advanced',
      'Professional'
    )
  ),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS progress_Log (
  log_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  log_date TEXT,
  logged_weight INTEGER,
  BMI REAL CHECK (BMI >= 0),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nutrition_log (
  entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  calories REAL,
  protein REAL,
  carbs REAL,
  fats REAL,
  fiber REAL,
  hydration REAL,
  similarity_score REAL,
  log_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS fitness_analyses (
  analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  analysis_date DATE NOT NULL,
  strength_score REAL,
  conditioning_score REAL,
  overall_score REAL,
  fitness_level TEXT,
  analysis_data TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS workout_plans (
  plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  duration_weeks INTEGER NOT NULL,
  sessions_per_week INTEGER NOT NULL,
  strength_ratio REAL NOT NULL,
  conditioning_ratio REAL NOT NULL,
  plan_data TEXT,
  active BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (user_id)
);
