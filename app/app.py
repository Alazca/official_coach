import datetime
import requests
import json
import os
import sqlite3
import openai

from flask import Flask, request, jsonify, render_template, redirect, url_for
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

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

app = Flask(
    __name__,
    static_folder=os.path.join(project_root, "frontend"),
    static_url_path="",
    template_folder=os.path.join(project_root, "frontend/pages"),
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
        print(f"Schema path: {full_schema_path}")

        # Delete the existing database file if it exists
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("✅ Existing database file deleted.")
            except Exception as e:
                print(f"❌ Failed to delete existing database: {e}")
                return

        # Create the database directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

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
    return redirect(url_for("frontpage"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/signup")
def sign_up():
    return render_template("signup.html")


@app.route("/login")
def login():
    return render_template("login.html")


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
            user_data.goal.value,
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
        return jsonify({"error": "User already exists"}), 400

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


@app.route("/api/strength-coach-chat", methods=["POST"])
def strength_coach_chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "No message provided."}), 400

        client = openai.OpenAI(api_key=app.config["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful and expert AI strength and conditioning coach. Answer questions about exercises, form, and provide workout recommendations.",
                },
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        ai_message = response.choices[0].message.content.strip()
        return jsonify({"response": ai_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/nutrition-coach-chat", methods=["POST"])
def nutrition_coach_chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "No message provided."}), 400

        client = openai.OpenAI(api_key=app.config["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful and expert AI nutrition coach. Answer questions about nutrition, meal planning, special diets, and provide healthy meal recommendations.",
                },
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        ai_message = response.choices[0].message.content.strip()
        return jsonify({"response": ai_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/food-search", methods=["POST"])
def food_search():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "No search query provided."}), 400

        api_key = "61iHOxJHfOiAmOCgg4gRbKwAAiIHt4JmnClvgdbb"  # Hard-coded for testing
        search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}"
        payload = {"query": query, "pageSize": 1}
        response = requests.post(search_url, json=payload)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from USDA API."}), 500
        results = response.json()
        if not results.get("foods"):
            return jsonify({"error": "No foods found."}), 404
        food = results["foods"][0]
        # Extract basic info
        food_info = {
            "description": food.get("description"),
            "brand": food.get("brandOwner"),
            "calories": None,
            "protein": None,
            "carbs": None,
            "fat": None,
        }
        for nutrient in food.get("foodNutrients", []):
            if nutrient.get("nutrientName") == "Energy":
                food_info["calories"] = nutrient.get("value")
            elif nutrient.get("nutrientName") == "Protein":
                food_info["protein"] = nutrient.get("value")
            elif nutrient.get("nutrientName") == "Carbohydrate, by difference":
                food_info["carbs"] = nutrient.get("value")
            elif nutrient.get("nutrientName") == "Total lipid (fat)":
                food_info["fat"] = nutrient.get("value")
        return jsonify(food_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/general-coach-chat", methods=["POST"])
def general_coach_chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "No message provided."}), 400

        client = openai.OpenAI(api_key=app.config["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful and expert AI assistant for the COACH fitness app. Your job is to help users decide if the COACH app is a good fit for their fitness, nutrition, and wellness needs. Ask about their goals, preferences, and challenges, and explain how COACH's features can help them. Be friendly, informative, and consultative.",
                },
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        ai_message = response.choices[0].message.content.strip()
        return jsonify({"response": ai_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
