import datetime
import requests
import json
import os
import sqlite3
import openai

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)

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
    create_conn,
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
    insert_workout,
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
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=7)
app.config["USDA_API_KEY"] = os.getenv("USDA_API_KEY")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
app.config["FOODDATA_API_KEY"] = os.getenv("FOODDATA_API_KEY")

jwt = JWTManager(app)
CORS(app, supports_credentials=True)


def initialize_database(schema_path: str = "backend/database/schema.sql") -> None:
    """
    Create the SQLite database (and apply schema) if it does not already exist.

    Args:
        schema_path (str): Relative path to schema.sql from project root.
    """
    config = Config()
    db_path = config.get_database_path()

    # Absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    full_schema_path = os.path.join(project_root, schema_path)

    # 1. If DB file already exists **and** at least one table is present, do nothing.
    if os.path.exists(db_path):
        try:
            with sqlite3.connect(db_path) as conn:
                # Quick existence check for a table you KNOW is in your schema
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
                )
                if cursor.fetchone():
                    print("✅ Database already initialized. Skipping.")
                    return
        except sqlite3.Error as e:
            # Fall through and recreate if file exists but is corrupt/empty
            print(f"⚠️  Existing DB found but validation failed ({e}); re‑initializing.")

    # 2. Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 3. Read and execute schema
    with open(full_schema_path, "r") as f:
        schema_sql = f.read()

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

    print("✅ Database initialized successfully.")


# Call only on application start‑up
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


@app.route("/logout")
def logout():
    return redirect("/")


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


@app.route("/get-workout")
def get_workout():
    return render_template("get_workout.html")


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
            # ← Generate JWT here
            access_token = create_access_token(
                identity=str(user_id),
                additional_claims={"email": user_data.email, "role": "user"},
            )
            return (
                jsonify(
                    {
                        "message": f"Successfully registered user {user_id}",
                        "access_token": access_token,
                    }
                ),
                200,
            )

        if isinstance(user_id, str):
            return jsonify({"Database error": f"{user_id}"}), 405

        if isinstance(user_id, str):
            return jsonify({"Database error": f"{user_id}"}), 405

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
        return jsonify({"error": "User already exists"}), 404

    if check_password_hash(data["password_hash"], password):
        additional_claims = {"email": data["email"], "role": "user"}

        access_token = create_access_token(
            identity=str(data["user_id"]), additional_claims=additional_claims
        )

        return (
            jsonify({"message": "Login successful", "access_token": access_token}),
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
            sleep=checkin.sleep,
            stress=checkin.stress,
            energy=checkin.energy,
            soreness=checkin.soreness,
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
    def describe_sleep(score):
        if score >= 9:
            return "Excellent"
        elif score >= 7:
            return "Good"
        elif score >= 5:
            return "Fair"
        else:
            return "Poor"

    def describe_energy(score):
        if score >= 9:
            return "Very High"
        elif score >= 7:
            return "High"
        elif score >= 5:
            return "Low"
        else:
            return "Very Low"

    try:
        user_id = get_jwt_identity()
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)

        if year is None or month is None:
            return jsonify({"error": "Missing year or month"}), 400

        all_checkins = get_all_checkins(user_id)
        filtered = []

        for c in all_checkins:
            checkin_date = datetime.strptime(c["check_in_date"], "%Y-%m-%d")
            if checkin_date.year == year and checkin_date.month == month:
                filtered.append(c)

        checkin_events = {}

        for c in filtered:
            date = datetime.strptime(c["check_in_date"], "%Y-%m-%d")
            y, m, d = date.year, date.month - 1, date.day

            checkin_events.setdefault(y, {}).setdefault(m, {})[d] = {}

            if c.get("sleep_quality") is not None:
                checkin_events[y][m][d]["sleep"] = describe_sleep(c["sleep_quality"])

            if c.get("energy_level") is not None:
                checkin_events[y][m][d]["energy"] = describe_energy(c["energy_level"])

        return jsonify(checkin_events), 200

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


from datetime import datetime


@app.route("/api/workouts", methods=["GET"])
@jwt_required()
def get_workouts():
    try:
        user_id = get_jwt_identity()
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)

        if year is None or month is None:
            return jsonify({"error": "Missing year or month parameter"}), 400

        # Get all workouts for this user
        all_workouts = get_workout_history(user_id)

        # Filter workouts by year and month
        filtered = []
        for w in all_workouts:
            workout_date = datetime.strptime(w["workout_date"], "%Y-%m-%d")
            if workout_date.year == year and workout_date.month == month:
                filtered.append(w)

        # Build nested structure for calendar: events[year][month][day] = {...}
        events = {}
        for w in filtered:
            workout_date = datetime.strptime(w["workout_date"], "%Y-%m-%d")
            y, m, d = workout_date.year, workout_date.month - 1, workout_date.day

            events.setdefault(y, {}).setdefault(m, {})[d] = {
                "workout": w["workout_type"],
                "readiness": 85,
            }

        return jsonify(events), 200

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

        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key not found in environment variables")
            return jsonify({"error": "OpenAI API key not configured"}), 500

        client = openai.OpenAI(api_key=api_key)

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

        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key not found in environment variables")
            return jsonify({"error": "OpenAI API key not configured"}), 500

        client = openai.OpenAI(api_key=api_key)
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

        # Get API key from environment variable
        api_key = os.getenv("FOODDATA_API_KEY")
        if not api_key:
            return jsonify({"error": "FoodData API key not configured"}), 500

        search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}"
        payload = {"query": query, "pageSize": 5}
        response = requests.post(search_url, json=payload)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from USDA API."}), 500
        results = response.json()
        if not results.get("foods"):
            return jsonify({"error": "No foods found."}), 404
        foods = []
        for food in results.get("foods", []):
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
            foods.append(food_info)
        return jsonify({"foods": foods})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/general-coach-chat", methods=["POST"])
def general_coach_chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "No message provided."}), 400
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OpenAI API key not found in environment variables")
            return jsonify({"error": "OpenAI API key not configured"}), 500

        client = openai.OpenAI(api_key=api_key)

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


@app.route("/api/workout/log", methods=["POST"])
@jwt_required()
def log_workout():
    try:
        data = request.get_json()
        print("Received workout data:", data)

        user_id = get_jwt_identity()

        workout_data = {
            "workout_type": data["workout_type"],
            "workout_date": data["workout_date"],
            "notes": data.get("notes", ""),
            "duration": data.get("duration", None),
            "user_id": user_id,
        }

        conn = create_conn()
        workout_id = insert_workout(conn, workout_data)
        conn.close()

        return jsonify({"success": True, "workout_id": workout_id}), 201

    except Exception as e:
        print("Error while logging workout:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
