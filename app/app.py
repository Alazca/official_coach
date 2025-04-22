import datetime
import os
import traceback
import sqlite3

from flask import Flask, request, jsonify, session,render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import request, redirect, render_template

from backend.database.db_utils import (
            get_all_checkins, get_workout_history, register_user, 
            insert_check_in, user_exists, validate_date
)
from backend.config.config import Config
from backend.models.models import UserRegistration, DailyCheckIn

from dotenv import load_dotenv
load_dotenv()

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


# Get the absolute path of the app.py file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to the project root directory (parent of app directory)
project_root = os.path.dirname(current_dir)

# Build the paths to static and templates folders
static_folder = os.path.join(project_root, 'frontend', 'static')
template_folder = os.path.join(project_root, 'frontend', 'templates')

# Create Flask app with absolute paths
app = Flask(__name__,
        static_folder=static_folder,
        template_folder=template_folder
)

initialize_database("backend/database/schema.sql")

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=7)
jwt = JWTManager(app)
CORS(app, supports_credentials=True)

@app.route("/")
def landing():
    return redirect("/login")

@app.route("/login")
def login_view():
    return render_template("login.html")

@app.route("/register")
def register_view():
    return render_template("register.html")

@app.route("/dashboard")
@jwt_required()
def dashboard_view():
    return render_template("/dashboard.html")


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
        print(ve.json())
        return jsonify({"Validation error": f"{str(ve)}"}), 400

    except Exception as e:
        traceback.print_exc()

        return jsonify({"Unexpected error": str(e)}), 500
    return jsonify({"error": "Unknown error occurred"}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    inputdata = request.get_json()
    email = inputdata.get('email', '')
    password = inputdata.get('password', '')

    # Check if user exists
    data = user_exists(email)

    if isinstance(data, Exception):
        return jsonify({"error": str(data)}), 500

    if data is None:
        return jsonify({"error": "User not found"}), 404

    if isinstance(data, str):  # Possibly a database error message
        return jsonify({"error": data}), 400

    # Verify password
    if check_password_hash(data['password_hash'], password):
        access_token = create_access_token(
            identity=str(data['user_id']),
            additional_claims={
                "email": data['email'],
                "role": "user"
            }
        )
        return jsonify({"message": "Login successful", "access token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/checkin', methods=['POST'])
@jwt_required()
def checkin():

    user_id = get_jwt_identity()
    data = request.get_json()
    checkin_data = DailyCheckIn(**data)

    check_in_date = str(datetime.datetime.now().date())
    checkin = insert_check_in(
        user_id=int(user_id),
        weight=checkin_data.weight,
        sleep=checkin_data.sleep,
        stress=checkin_data.stress,
        energy=checkin_data.energy,
        soreness=checkin_data.soreness,
        check_in_date = check_in_date

    )

    if isinstance(checkin, str):
        return jsonify({"error": checkin}), 400

    if isinstance(checkin, int):
        return jsonify({"message": "checkin recorded successfully."}), 200


@app.route('/api/checkin/history', methods=["GET"])
@jwt_required()
def get_checkin():
    user_id = get_jwt_identity()
    end_date = request.args.get('enddate', None)
    start_date = request.args.get('startdate', None)

    checkins = get_all_checkins(user_id=int(user_id), start_date=start_date, end_date=end_date)
    if isinstance(checkins, Exception):
        return jsonify({"error": f'{str(checkins)}'})

    return jsonify({"message": checkins}), 200


@app.route('/api/workout/history', methods=['GET'])
@jwt_required()
def workout_history():
    ed = request.args.get('enddate', None)
    sd = request.args.get('startdate', None)
    user_id = get_jwt_identity()
    workouts = get_workout_history(user_id=user_id, enddate=ed, startdate=sd)
    if isinstance(workouts, list):
        return jsonify({"workouts": workouts}), 200
    if isinstance(workouts, str):
        return jsonify({"Database error": workouts}), 400

@app.route("/api/readiness/vector")
@jwt_required()
def get_vector_for_date():
    user_id = get_jwt_identity()
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "Date required"}), 400

    # Dummy data for test (replace with real vector call)
    return jsonify({
        "date": date,
        "vector": [7, 3, 2, 8],  # readiness, stress, soreness, sleep
        "score": 0.85
    }), 200


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
