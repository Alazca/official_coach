import datetime
import requests
import json
import os
import sqlite3

from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from backend.config.config import Config
from backend.database.db import get_all_checkins, get_workout_history, register_user, insert_check_in, user_exists, validate_date, get_nutrition_history, get_weight_history, get_exercise_distribution
from backend.models.models import UserRegistration, DailyCheckIn
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__,
            static_folder='../frontend',
            static_url_path='/assets',
            template_folder='../frontend/pages'
)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=7)
app.config['USDA_API_KEY'] = os.getenv('USDA_API_KEY')
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
jwt = JWTManager(app)
CORS(app, supports_credentials=True)

def initialize_database(schema_path: str = "backend/database/schema.sql") -> None:
    """
    Initialize the database schema from a .sql file.

    Args:
        schema_path (str): Path to the schema.sql file
    """
    try:
        config = Config()
        db_path = config.get_database_path()

        # Get absolute path to project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        # Build absolute path to schema.sql
        full_schema_path = os.path.join(project_root, schema_path)

        with open(full_schema_path, "r") as f:
            schema = f.read()

        with sqlite3.connect(db_path) as conn:
            conn.executescript(schema)
            conn.commit()

        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")

initialize_database("backend/database/schema.sql")

@app.route('/')
def index():
    """Serve the frontpage of the application"""
    return render_template('frontpage.html')

@app.route('/signup')
def signup_page():
    return render_template('sign-up.html')

@app.route('/workout')
def workout_page():
    """Serve the workout of the day page"""
    return render_template('workout_of_the_day.html')

@app.route('/nutrition')
def nutrition_page():
    """Serve the log food page"""
    return render_template('log_food.html')

@app.route('/visualize')
def visualize_page():
    """Serve the data visualization page"""
    return render_template('visualize_data.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        user_data = UserRegistration(**data)
        password_hash = generate_password_hash(user_data.password)
        user_id = register_user(
            user_data.email,
            password_hash,
            user_data.name,
            user_data.gender.value,
            user_data.dob,
            user_data.height,
            user_data.weight,
            user_data.initialActivityLevel.value
        )
        if isinstance(user_id, int):
            return jsonify({"message": f"Successfully registered user {user_id}"}), 200

        if isinstance(user_id, str):
            return jsonify({"Database error": f"{user_id}"}), 400

    except ValueError as ve:
        return jsonify({"Validation error": f"{str(ve)}"}), 400

    except Exception as e:
        return jsonify({"Unexpected error": str(e)}), 500
    return jsonify({"error": "Unknown error occurred"}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    inputdata = request.get_json()
    email = inputdata.get('email', '')
    password = inputdata.get('password', '')
    data = user_exists(email)
    if isinstance(data, Exception):
        return jsonify({"error": f"{str(data)}"}), 400
    if not data:
        return jsonify({"error": "User already exists"}), 400

    if check_password_hash(data['password_hash'], password):
        additional_claims = {
            "email": data['email'],
            "role": "user"
        }

        access_token = create_access_token(identity=str(data['user_id']),
                                           additional_claims=additional_claims
                                           )


        return jsonify({"message": "Login successful", "access token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
