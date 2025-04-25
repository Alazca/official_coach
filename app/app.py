import datetime
import requests
import json
import os
import sqlite3

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from dotenv import load_dotenv

from backend.config.config import Config
from backend.database.db import (
    get_all_checkins,
    get_workout_history,
    register_user,
    insert_check_in,
    user_exists,
    validate_date,
    get_nutrition_history,
    get_weight_history,
    get_exercise_distribution,
    get_user_goals,
)

from backend.models.models import UserRegistration, DailyCheckIn

load_dotenv()


app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path="/assets",
    template_folder="../frontend/pages",
)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=7)
app.config["USDA_API_KEY"] = os.getenv("USDA_API_KEY")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")


@app.route("/frontpage")
def frontpage():
    return render_template("frontpage.html")


@app.route("/log-food")
def log_food():
    return render_template("log_food.html")


@app.route("/metrics-menu")
def metrics_menu():
    return render_template("metrics_menu.html")


@app.route("/nutrition-hub")
def nutrition_hub():
    return render_template("nutrition_hub.html")


@app.route("/strength-conditioning-hub")
def strength_conditioning_hub():
    return render_template("strength_conditioning_hub.html")


@app.route("/head-coach-hub")
def head_coach_hub():
    return render_template("head_coach_hub.html")


@app.route("/visualize-data")
def visualize_data():
    return render_template("visualize_data.html")


@app.route("/workout-of-the-day")
def workout_of_the_day():
    return render_template("workout_of_the_day.html")


@app.route("/api/register", methods=["POST"])
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
            user_data.initialActivityLevel.value,
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


@app.route("/api/login", methods=["POST"])
def login_user():
    inputdata = request.get_json()
    email = inputdata.get("email", "")
    password = inputdata.get("password", "")
    data = user_exists(email)
    if isinstance(data, Exception):
        return jsonify({"error": f"{str(data)}"}), 400
    if not data:
        return jsonify({"error": "User does not exist"}), 404

    if check_password_hash(data["password_hash"], password):
        additional_claims = {"email": data["email"], "role": "user"}

        access_token = create_access_token(
            identity=str(data["user_id"]), additional_claims=additional_claims
        )

        return (
            jsonify({"message": "Login successful", "access token": access_token}),
            200,
        )
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/check-in", methods=["POST"])
@jwt_required()
def check_in():
    try:
        data = request.get_json()
        checkin = DailyCheckIn(**data)
        user_id = get_jwt_identity()

        checkin_id = insert_check_in(
            user_id=user_id,
            weight=checkin.weight,
            sleep=checkin.sleep_quality,
            stress=checkin.stress_level,
            energy=checkin.energy_level,
            soreness=checkin.soreness_level,
            check_in_date=checkin.check_in_date,
        )
        return jsonify({"message": "Check-in recorded", "checkin_id": checkin_id}), 200
    except ValueError as ve:
        return jsonify({"Validation error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/check-ins", methods=["GET"])
@jwt_required()
def get_check_ins():
    try:
        user_id = get_jwt_identity()
        checkins = get_all_checkins(user_id)
        return jsonify(checkins), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/goals", methods=["GET"])
@jwt_required()
def get_goals():
    try:
        user_id = get_jwt_identity()
        goals = get_user_goals(user_id)
        return jsonify(goals), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/workouts", methods=["GET"])
@jwt_required()
def get_workouts():
    try:
        user_id = get_jwt_identity()
        history = get_workout_history(user_id)
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/nutrition", methods=["GET"])
@jwt_required()
def get_nutrition():
    try:
        user_id = get_jwt_identity()
        nutrition = get_nutrition_history(user_id)
        return jsonify(nutrition), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)

# for testing /api/me rout to get info of current user
@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    identity = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "user_id": identity,
        "email": claims["email"]
    }), 200

# for testing /api/checkin to check for successful checkin
@app.route('/api/checkin', methods=['POST'])
@jwt_required()
def submit_checkin():
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['weight', 'sleep', 'stress', 'energy', 'soreness']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required check-in fields"}), 400

    try:
        insert_check_in(
            user_id=user_id,
            weight=data['weight'],
            sleep=data['sleep'],
            stress=data['stress'],
            energy=data['energy'],
            soreness=data['soreness'],
            check_in_date=str(datetime.date.today())
        )
        return jsonify({"message": "Check-in saved successfully"}), 200
    except Exception as e:
        print("CHECK-IN ERROR:", e)  # 👈 Add this line
        return jsonify({"error": f"Failed to insert check-in: {str(e)}"}), 500

# for testing if user can fetch all checkins
@app.route('/api/checkins/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_checkins(user_id):
    current_user = get_jwt_identity()
    if int(current_user) != user_id:
        return jsonify({"error": "Unauthorized access to another user's data"}), 403

    try:
        checkins = get_all_checkins(user_id)
        return jsonify(checkins), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch check-ins: {str(e)}"}), 500
    
# for testing route to get workout history
@app.route('/api/workout-history', methods=['GET'])
@jwt_required()
def workout_history():
    user_id = get_jwt_identity()
    try:
        history = get_workout_history(user_id)
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get workout history: {str(e)}"}), 500