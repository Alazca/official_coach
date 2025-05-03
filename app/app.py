import datetime
import requests
import json
import os
import sqlite3
import logging

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
    insert_workout,
    insert_workout_sets,
)

from backend.models.models import UserRegistration, DailyCheckIn

# Add imports for vector-based fitness tracking
from backend.engines.user_vector import (
    get_user_vector,
    update_user_vector,
    save_vector_snapshot,
    analyze_vector_trends,
)
from backend.engines.target_vector import (
    initialize_target_vector,
    get_target_vector,
    get_user_targets,
    get_current_milestone,
    calculate_goal_progress,
    update_target_vector,
    generate_goal_recommendations,
    create_goal_from_recommendation,
    archive_completed_goals,
)
from backend.engines.metrics import (
    get_strength_metrics,
    get_conditioning_metrics,
    get_readiness_metrics,
    get_workout_distribution,
    get_performance_trend,
)
from backend.engines.scalars import (
    compute_influence_scalars,
    compute_final_scalar,
    classify_overall_fitness_tier,
)

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)

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

        logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")


initialize_database("backend/database/schema.sql")


# -------------------------------------------------------
# Page Routes
# -------------------------------------------------------


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


@app.route("/goals")
def goals():
    return render_template("goals.html")


# -------------------------------------------------------
# Authentication API Routes
# -------------------------------------------------------


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
            user_data.goal.value if hasattr(user_data, "goal") else None,
        )
        if isinstance(user_id, int):
            # Initialize user vector and create default goal
            try:
                user_vector = update_user_vector(user_id)
                save_vector_snapshot(user_id)

                # Create initial goal based on user's selected goal type
                if hasattr(user_data, "goal"):
                    target = initialize_target_vector(
                        user_id=user_id,
                        goal_type=user_data.goal,
                        target_date=datetime.date.today()
                        + datetime.timedelta(days=90),  # 90-day initial goal
                    )

                logger.info(f"Successfully created vector profile for user {user_id}")
            except Exception as e:
                logger.error(f"Error initializing vector profile: {str(e)}")

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Successfully registered user {user_id}",
                        "user_id": user_id,
                    }
                ),
                200,
            )

        if isinstance(user_id, str):
            return (
                jsonify({"success": False, "error": f"Database error: {user_id}"}),
                400,
            )

    except ValueError as ve:
        return jsonify({"success": False, "error": f"Validation error: {str(ve)}"}), 400

    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

    return jsonify({"success": False, "error": "Unknown error occurred"}), 500


@app.route("/api/login", methods=["POST"])
def login_user():
    try:
        inputdata = request.get_json()
        email = inputdata.get("email", "")
        password = inputdata.get("password", "")
        data = user_exists(email)

        if isinstance(data, Exception):
            return jsonify({"success": False, "error": f"{str(data)}"}), 400
        if not data:
            return jsonify({"success": False, "error": "User not found"}), 404

        if check_password_hash(data["password_hash"], password):
            additional_claims = {"email": data["email"], "role": "user"}

            access_token = create_access_token(
                identity=str(data["user_id"]), additional_claims=additional_claims
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Login successful",
                        "access_token": access_token,
                        "user_id": data["user_id"],
                        "name": data.get("name", ""),
                    }
                ),
                200,
            )
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "error": f"Login error: {str(e)}"}), 500


# -------------------------------------------------------
# Daily Check-in API Routes
# -------------------------------------------------------


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
            check_in_date=(
                datetime.date.today().isoformat()
                if not hasattr(checkin, "check_in_date")
                else checkin.check_in_date
            ),
        )

        # Update user vector after check-in
        try:
            user_vector = update_user_vector(user_id)
            save_vector_snapshot(user_id)
        except Exception as e:
            logger.error(f"Error updating user vector after check-in: {str(e)}")

        # Calculate readiness score based on checkin
        readiness_level = int(
            ((checkin.sleep + checkin.energy - checkin.stress - checkin.soreness) / 20)
            * 100
        )
        readiness_level = max(0, min(100, readiness_level))  # Clamp to 0-100

        # Calculate contributing factors
        factors = {
            "sleep": checkin.sleep / 10,  # Scale to 0-1
            "energy": checkin.energy / 10,
            "stress": (10 - checkin.stress) / 10,  # Invert so higher is better
            "soreness": (10 - checkin.soreness) / 10,  # Invert so higher is better
        }

        # Identify areas to focus on
        focus_areas = []
        if factors["sleep"] < 0.6:
            focus_areas.append("sleep")
        if factors["stress"] < 0.5:
            focus_areas.append("stress_management")
        if factors["soreness"] < 0.4:
            focus_areas.append("recovery")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Check-in recorded",
                    "checkin_id": checkin_id,
                    "readiness_score": readiness_level,
                    "contributing_factors": factors,
                    "focus_areas": focus_areas,
                }
            ),
            200,
        )
    except ValueError as ve:
        return jsonify({"success": False, "error": f"Validation error: {str(ve)}"}), 400
    except Exception as e:
        logger.error(f"Check-in error: {str(e)}")
        return jsonify({"success": False, "error": f"Check-in error: {str(e)}"}), 500


@app.route("/api/check-ins", methods=["GET"])
@jwt_required()
def get_check_ins():
    try:
        user_id = get_jwt_identity()
        checkins = get_all_checkins(user_id)
        return jsonify({"success": True, "checkins": checkins}), 200
    except Exception as e:
        logger.error(f"Error retrieving check-ins: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------
# Workout API Routes
# -------------------------------------------------------


@app.route("/api/workouts", methods=["GET"])
@jwt_required()
def get_workouts():
    try:
        user_id = get_jwt_identity()
        history = get_workout_history(user_id)
        return jsonify({"success": True, "workouts": history}), 200
    except Exception as e:
        logger.error(f"Error retrieving workouts: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/workout/log", methods=["POST"])
@jwt_required()
def log_workout():
    """
    Record a completed workout and update user vector.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        required_fields = ["workout_type", "exercises"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {"success": False, "error": f"Missing required field: {field}"}
                    ),
                    400,
                )

        workout_date = data.get(
            "workout_date", datetime.datetime.now().strftime("%Y-%m-%d")
        )
        workout_type = data.get("workout_type")
        notes = data.get("notes", "")
        exercises = data.get("exercises", [])

        # Insert workout
        workout_id = insert_workout(
            user_id=int(user_id),
            workout_date=workout_date,
            workout_type=workout_type,
            notes=notes,
        )

        # Insert workout sets for each exercise
        for exercise in exercises:
            exercise_id = exercise.get("exercise_id")
            sets = exercise.get("sets", 1)
            reps = exercise.get("reps", 1)
            weight = exercise.get("weight", 0)
            is_one_rm = exercise.get("is_one_rm", 0)

            insert_workout_sets(
                workout_id=workout_id,
                exercise_id=exercise_id,
                lifting_weight=weight,
                sets=sets,
                reps=reps,
                is_one_rm=1 if is_one_rm else 0,
            )

        # Update user vector
        user_vector = update_user_vector(int(user_id))
        save_vector_snapshot(int(user_id))

        # Get updated metrics
        strength_metrics = get_strength_metrics(int(user_id))
        conditioning_metrics = get_conditioning_metrics(int(user_id))

        # Calculate workout stats
        total_volume = sum(
            exercise.get("sets", 1)
            * exercise.get("reps", 1)
            * exercise.get("weight", 0)
            for exercise in exercises
        )

        total_reps = sum(
            exercise.get("sets", 1) * exercise.get("reps", 1) for exercise in exercises
        )

        workout_stats = {
            "total_volume": total_volume,
            "total_exercises": len(exercises),
            "total_reps": total_reps,
            "avg_intensity": total_volume / total_reps if total_reps > 0 else 0,
        }

        # Update progress on active goals
        active_goals = get_user_targets(int(user_id))
        goal_updates = []

        for goal in active_goals:
            try:
                target_id = goal.get("target_id")
                progress = calculate_goal_progress(int(user_id), target_id)
                goal_updates.append(
                    {
                        "target_id": target_id,
                        "goal_type": goal.get("goal_type"),
                        "progress": progress.get("vector_progress_pct", 0),
                        "on_track": progress.get("on_track", False),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Error calculating progress for goal {goal.get('target_id')}: {str(e)}"
                )

        return (
            jsonify(
                {
                    "success": True,
                    "workout_id": workout_id,
                    "workout_stats": workout_stats,
                    "updated_metrics": {
                        "strength": strength_metrics,
                        "conditioning": conditioning_metrics,
                    },
                    "goal_updates": goal_updates,
                    "fitness_level": (
                        user_vector.activity_level if user_vector else "Unknown"
                    ),
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error logging workout: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------
# Nutrition API Routes
# -------------------------------------------------------


@app.route("/api/nutrition", methods=["GET"])
@jwt_required()
def get_nutrition():
    try:
        user_id = get_jwt_identity()
        nutrition = get_nutrition_history(user_id)
        return jsonify({"success": True, "nutrition": nutrition}), 200
    except Exception as e:
        logger.error(f"Error retrieving nutrition: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------
# Goal Management API Routes
# -------------------------------------------------------


@app.route("/api/goals", methods=["GET"])
@jwt_required()
def get_goals():
    try:
        user_id = get_jwt_identity()
        goals = get_user_targets(int(user_id))
        return jsonify({"success": True, "goals": goals}), 200
    except Exception as e:
        logger.error(f"Error retrieving goals: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/goals/create", methods=["POST"])
@jwt_required()
def create_new_goal():
    """
    Create a new fitness goal for user.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        required_fields = ["goal_type", "target_date"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {"success": False, "error": f"Missing required field: {field}"}
                    ),
                    400,
                )

        # Extract data
        goal_type = data.get("goal_type")
        target_date = data.get("target_date")
        custom_dimensions = data.get("custom_dimensions")
        description = data.get("description")

        # Create target vector
        target = initialize_target_vector(
            user_id=int(user_id),
            goal_type=goal_type,
            target_date=target_date,
            custom_dimensions=custom_dimensions,
            description=description,
        )

        if not target:
            return jsonify({"success": False, "error": "Failed to create goal"}), 500

        # Calculate initial progress
        progress = calculate_goal_progress(int(user_id), target.target_id)

        return (
            jsonify(
                {
                    "success": True,
                    "goal": {
                        "target_id": target.target_id,
                        "goal_type": goal_type,
                        "target_date": target_date,
                        "description": description,
                        "dimensions": [
                            {"name": dim, "value": val}
                            for dim, val in zip(target.dimensions, target.vector)
                        ],
                        "milestones": target.milestones,
                        "current_progress": progress.get("vector_progress_pct", 0),
                        "on_track": progress.get("on_track", False),
                    },
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error creating goal: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/goals/<int:target_id>", methods=["GET"])
@jwt_required()
def get_goal_details(target_id):
    """
    Get detailed information about a specific goal.
    """
    try:
        user_id = get_jwt_identity()

        # Get target vector
        target = get_target_vector(target_id)

        if not target or target.user_id != int(user_id):
            return (
                jsonify({"success": False, "error": "Goal not found or unauthorized"}),
                404,
            )

        # Get current milestone
        milestone = get_current_milestone(target_id)

        # Calculate progress
        progress = calculate_goal_progress(int(user_id), target_id)

        return (
            jsonify(
                {
                    "success": True,
                    "goal": {
                        "target_id": target_id,
                        "goal_type": (
                            target.goal_type.value
                            if hasattr(target.goal_type, "value")
                            else target.goal_type
                        ),
                        "target_date": (
                            target.target_date.isoformat()
                            if hasattr(target.target_date, "isoformat")
                            else target.target_date
                        ),
                        "description": (
                            target.description if hasattr(target, "description") else ""
                        ),
                        "status": (
                            target.status if hasattr(target, "status") else "active"
                        ),
                        "created_at": target.created_at,
                        "current_milestone": {
                            "percent": milestone.percent if milestone else 0,
                            "date": (
                                milestone.date.isoformat()
                                if hasattr(milestone, "date")
                                and hasattr(milestone.date, "isoformat")
                                else None
                            ),
                        },
                        "progress": {
                            "overall_progress": progress.get("vector_progress_pct", 0),
                            "time_progress": progress.get("time_progress_pct", 0),
                            "on_track": progress.get("on_track", False),
                            "days_remaining": progress.get("days_remaining", 0),
                            "status": progress.get("status", "unknown"),
                            "projected_completion": progress.get(
                                "projected_completion"
                            ),
                        },
                        "dimension_progress": progress.get("dimension_progress", []),
                        "milestones": target.milestones,
                        "similarity": progress.get("similarity", {}),
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error getting goal details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/goals/<int:target_id>", methods=["PUT"])
@jwt_required()
def update_goal(target_id):
    """
    Update an existing goal.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Get target vector
        target = get_target_vector(target_id)

        if not target or target.user_id != int(user_id):
            return (
                jsonify({"success": False, "error": "Goal not found or unauthorized"}),
                404,
            )

        # Extract update data
        custom_dimensions = data.get("custom_dimensions")
        extend_days = data.get("extend_days")
        new_description = data.get("description")
        status = data.get("status")

        # Update target
        updated = update_target_vector(
            target_id=target_id,
            custom_dimensions=custom_dimensions,
            extend_target_date=extend_days,
            new_description=new_description,
            status=status,
        )

        if not updated:
            return jsonify({"success": False, "error": "Failed to update goal"}), 500

        # Get updated progress
        progress = calculate_goal_progress(int(user_id), target_id)

        return (
            jsonify(
                {
                    "success": True,
                    "goal": {
                        "target_id": target_id,
                        "goal_type": (
                            updated.goal_type.value
                            if hasattr(updated.goal_type, "value")
                            else updated.goal_type
                        ),
                        "target_date": (
                            updated.target_date.isoformat()
                            if hasattr(updated.target_date, "isoformat")
                            else updated.target_date
                        ),
                        "status": (
                            updated.status if hasattr(updated, "status") else "active"
                        ),
                        "progress": {
                            "overall_progress": progress.get("vector_progress_pct", 0),
                            "on_track": progress.get("on_track", False),
                        },
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error updating goal: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/goals/recommendations", methods=["GET"])
@jwt_required()
def get_goal_recommendations():
    """
    Get personalized goal recommendations.
    """
    try:
        user_id = get_jwt_identity()
        focus_area = request.args.get("focus_area")
        limit = request.args.get("limit", 3, type=int)

        recommendations = generate_goal_recommendations(
            user_id=int(user_id), focus_area=focus_area, limit=limit
        )

        # Assign unique IDs to recommendations for frontend reference
        for i, rec in enumerate(recommendations):
            rec["id"] = i + 1

        return jsonify({"success": True, "recommendations": recommendations}), 200
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/goals/from-recommendation", methods=["POST"])
@jwt_required()
def create_from_recommendation():
    """
    Create a goal from a recommendation.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        if "recommendation_id" not in data:
            return (
                jsonify({"success": False, "error": "Missing recommendation_id"}),
                400,
            )

        recommendation_id = data.get("recommendation_id")
        custom_duration = data.get("duration")

        # Create goal
        target = create_goal_from_recommendation(
            user_id=int(user_id),
            recommendation_id=recommendation_id,
            custom_duration=custom_duration,
        )

        if not target:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to create goal from recommendation",
                    }
                ),
                500,
            )

        # Calculate initial progress
        progress = calculate_goal_progress(int(user_id), target.target_id)

        return (
            jsonify(
                {
                    "success": True,
                    "goal": {
                        "target_id": target.target_id,
                        "goal_type": (
                            target.goal_type.value
                            if hasattr(target.goal_type, "value")
                            else target.goal_type
                        ),
                        "target_date": (
                            target.target_date.isoformat()
                            if hasattr(target.target_date, "isoformat")
                            else target.target_date
                        ),
                        "dimensions": [
                            {"name": dim, "value": val}
                            for dim, val in zip(target.dimensions, target.vector)
                        ],
                        "current_progress": progress.get("vector_progress_pct", 0),
                        "on_track": progress.get("on_track", False),
                    },
                }
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Error creating goal from recommendation: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------
# Dashboard and Metrics API Routes
# -------------------------------------------------------


@app.route("/api/dashboard/data", methods=["GET"])
@jwt_required()
def get_dashboard_data():
    """
    Get comprehensive dashboard data for user.
    """
    try:
        user_id = get_jwt_identity()

        # Update user vector to ensure freshness
        user_vector = update_user_vector(int(user_id))
        if not user_vector:
            return (
                jsonify({"success": False, "error": "Failed to generate user vector"}),
                500,
            )

        # Get metrics
        strength_metrics = get_strength_metrics(int(user_id))
        conditioning_metrics = get_conditioning_metrics(int(user_id))
        readiness_metrics = get_readiness_metrics(int(user_id), days=7)
        workout_distribution = get_workout_distribution(int(user_id), days=30)

        # Get goals and progress
        goals = get_user_targets(int(user_id))
        goal_progress = []

        for goal in goals:
            target_id = goal.get("target_id")
            try:
                progress = calculate_goal_progress(int(user_id), target_id)
                goal_progress.append(
                    {
                        "target_id": target_id,
                        "goal_type": goal.get("goal_type"),
                        "target_date": goal.get("target_date"),
                        "progress": progress.get("vector_progress_pct", 0),
                        "on_track": progress.get("on_track", False),
                        "days_remaining": progress.get("days_remaining", 0),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Error calculating progress for goal {target_id}: {str(e)}"
                )

        # Get trend analysis
        trends = analyze_vector_trends(int(user_id))

        # Get recommendations
        recommendations = generate_goal_recommendations(int(user_id))

        # Archive any completed goals
        archived_count = archive_completed_goals(int(user_id))

        return (
            jsonify(
                {
                    "success": True,
                    "fitness_level": user_vector.activity_level,
                    "metrics": {
                        "strength": strength_metrics,
                        "conditioning": conditioning_metrics,
                        "readiness": readiness_metrics,
                        "distribution": workout_distribution,
                    },
                    "goal_progress": goal_progress,
                    "trends": trends,
                    "recommendations": recommendations,
                    "archived_goals": archived_count,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vector/user", methods=["GET"])
@jwt_required()
def get_user_vector_api():
    """
    Get user's current vector representation.
    """
    try:
        user_id = get_jwt_identity()
        user_vector = get_user_vector(int(user_id))

        if not user_vector:
            # Create a new vector if none exists
            user_vector = update_user_vector(int(user_id))

        if not user_vector:
            return (
                jsonify({"success": False, "error": "Failed to retrieve user vector"}),
                500,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "vector": {
                        "dimensions": user_vector.dimensions,
                        "values": user_vector.vector,
                        "fitness_level": user_vector.activity_level,
                        "final_scalar": user_vector.final_scalar,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error retrieving user vector: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vector/trends", methods=["GET"])
@jwt_required()
def get_vector_trends():
    """
    Get user vector trend analysis.
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 90, type=int)

        trends = analyze_vector_trends(int(user_id), days=days)

        return jsonify({"success": True, "trends": trends}), 200
    except Exception as e:
        logger.error(f"Error analyzing vector trends: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics/readiness", methods=["GET"])
@jwt_required()
def get_readiness():
    """
    Get readiness metrics from daily check-ins.
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 7, type=int)

        readiness = get_readiness_metrics(int(user_id), days)

        return jsonify({"success": True, "readiness": readiness}), 200
    except Exception as e:
        logger.error(f"Error getting readiness metrics: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics/strength", methods=["GET"])
@jwt_required()
def get_strength():
    """
    Get strength metrics.
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 7, type=int)

        metrics = get_strength_metrics(int(user_id), days)

        return jsonify({"success": True, "metrics": metrics}), 200
    except Exception as e:
        logger.error(f"Error getting strength metrics: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics/conditioning", methods=["GET"])
@jwt_required()
def get_conditioning():
    """
    Get conditioning metrics.
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 7, type=int)

        metrics = get_conditioning_metrics(int(user_id), days)

        return jsonify({"success": True, "metrics": metrics}), 200
    except Exception as e:
        logger.error(f"Error getting conditioning metrics: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics/performance/<exercise_name>", methods=["GET"])
@jwt_required()
def get_performance(exercise_name):
    """
    Get performance trend for a specific exercise.
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 90, type=int)

        trend = get_performance_trend(int(user_id), exercise_name, days)

        return jsonify({"success": True, "trend": trend}), 200
    except Exception as e:
        logger.error(f"Error getting performance trend: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/metrics/workout-distribution", methods=["GET"])
@jwt_required()
def get_workout_dist():
    """
    Get workout type distribution and frequency.
    """
    try:
        user_id = get_jwt_identity()
        days = request.args.get("days", 30, type=int)

        distribution = get_workout_distribution(int(user_id), days)

        return jsonify({"success": True, "distribution": distribution}), 200
    except Exception as e:
        logger.error(f"Error getting workout distribution: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/workout/recommendations", methods=["GET"])
@jwt_required()
def get_workout_recommendations():
    """
    Get personalized workout recommendations based on user profile and goals.
    """
    try:
        user_id = get_jwt_identity()
        goal_id = request.args.get("goal_id", type=int)

        # Get user vector and fitness level
        user_vector = get_user_vector(int(user_id))

        if not user_vector:
            return jsonify({"success": False, "error": "User vector not found"}), 404

        fitness_level = user_vector.activity_level or "Beginner"

        # Get readiness score for today
        with create_conn() as conn:
            cur = conn.cursor()
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                """
                SELECT readiness_level
                FROM readiness_scores
                WHERE user_id = ? AND readiness_date = ?
                """,
                (user_id, current_date),
            )
            row = cur.fetchone()

        readiness = row[0] if row else 70  # Default to 70 if no reading

        # Determine workout difficulty based on readiness
        if readiness >= 80:
            difficulty = "challenging"
        elif readiness >= 60:
            difficulty = "moderate"
        else:
            difficulty = "recovery"

        # Get recent workout history
        with create_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT workout_date, workout_type 
                FROM workouts
                WHERE user_id = ?
                ORDER BY workout_date DESC
                LIMIT 7
                """,
                (user_id,),
            )
            recent_workouts = cur.fetchall()

        # Check if we've trained recently
        recent_dates = [row[0] for row in recent_workouts]
        recent_types = [row[1] for row in recent_workouts]

        # Get current goal type
        current_goal_type = None
        if goal_id:
            target = get_target_vector(goal_id)
            if target and target.user_id == int(user_id):
                current_goal_type = (
                    target.goal_type.value
                    if hasattr(target.goal_type, "value")
                    else target.goal_type
                )
        else:
            # Get most recent goal
            goals = get_user_targets(int(user_id))
            if goals:
                current_goal_type = goals[0].get("goal_type")

        # Default to strength if no goal
        if not current_goal_type:
            current_goal_type = "Strength"

        # Select workout type based on goal and recent history
        if current_goal_type == "Strength":
            workout_types = [
                "Strength",
                "Strength",
                "Recovery",
                "Strength",
                "Conditioning",
            ]
        elif current_goal_type == "Endurance":
            workout_types = [
                "Conditioning",
                "Conditioning",
                "Recovery",
                "Strength",
                "Conditioning",
            ]
        elif current_goal_type == "Weight-Loss":
            workout_types = [
                "Conditioning",
                "Strength",
                "Conditioning",
                "Recovery",
                "Conditioning",
            ]
        elif current_goal_type == "Performance":
            workout_types = [
                "Strength",
                "Conditioning",
                "Strength",
                "Recovery",
                "Conditioning",
            ]
        else:  # Default
            workout_types = [
                "Strength",
                "Conditioning",
                "Recovery",
                "Strength",
                "Conditioning",
            ]

        # Check recent workout types to avoid repetition
        if recent_types:
            latest_type = recent_types[0]

            # Avoid same type consecutively unless recovery
            if latest_type != "Recovery" and latest_type in workout_types:
                # Move the recent type down in priority
                workout_types.remove(latest_type)
                workout_types.append(latest_type)

        # Override with recovery if readiness is very low
        if readiness < 40:
            recommended_type = "Recovery"
        else:
            # Select workout type based on adjusted priorities
            if difficulty == "recovery":
                recommended_type = "Recovery"
            else:
                # Use the first prioritized type
                recommended_type = workout_types[0]

        # Get recommended exercises from database
        # This part will depend on your database schema for exercises
        with create_conn() as conn:
            cur = conn.cursor()

            if recommended_type == "Strength":
                cur.execute(
                    """
                    SELECT exercise_id, name, category, muscle_group
                    FROM exercises
                    WHERE category IN ('Compound', 'Olympic-Style')
                    ORDER BY RANDOM()
                    LIMIT 5
                    """
                )
            elif recommended_type == "Conditioning":
                cur.execute(
                    """
                    SELECT exercise_id, name, category, muscle_group
                    FROM exercises
                    WHERE category IN ('Compound', 'Cardio')
                    ORDER BY RANDOM()
                    LIMIT 6
                    """
                )
            else:  # Recovery
                cur.execute(
                    """
                    SELECT exercise_id, name, category, muscle_group
                    FROM exercises
                    WHERE category IN ('Mobility', 'Isolation')
                    ORDER BY RANDOM()
                    LIMIT 4
                    """
                )

            exercises = [
                {
                    "exercise_id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "muscle_group": row[3],
                }
                for row in cur.fetchall()
            ]

        # Add sets/reps/weight recommendations based on workout type and difficulty
        for exercise in exercises:
            if recommended_type == "Strength":
                if difficulty == "challenging":
                    exercise["sets"] = 4
                    exercise["reps"] = "5-8"
                    exercise["intensity"] = "80-85%"
                elif difficulty == "moderate":
                    exercise["sets"] = 3
                    exercise["reps"] = "8-12"
                    exercise["intensity"] = "70-75%"
                else:  # recovery
                    exercise["sets"] = 2
                    exercise["reps"] = "12-15"
                    exercise["intensity"] = "60-65%"
            elif recommended_type == "Conditioning":
                if difficulty == "challenging":
                    exercise["sets"] = 5
                    exercise["reps"] = "30-45 sec"
                    exercise["intensity"] = "High"
                elif difficulty == "moderate":
                    exercise["sets"] = 4
                    exercise["reps"] = "40-60 sec"
                    exercise["intensity"] = "Moderate"
                else:  # recovery
                    exercise["sets"] = 3
                    exercise["reps"] = "30-40 sec"
                    exercise["intensity"] = "Low"
            else:  # Recovery
                exercise["sets"] = 2
                exercise["reps"] = "10-12"
                exercise["intensity"] = "Very Light"

        # Create workout plan response
        workout_plan = {
            "type": recommended_type,
            "difficulty": difficulty,
            "readiness_score": readiness,
            "goal_type": current_goal_type,
            "exercises": exercises,
            "notes": _generate_workout_notes(
                readiness, recommended_type, difficulty, fitness_level
            ),
        }

        return jsonify({"success": True, "workout_plan": workout_plan}), 200
    except Exception as e:
        logger.error(f"Error generating workout recommendations: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def _generate_workout_notes(
    readiness: int, workout_type: str, difficulty: str, fitness_level: str
) -> str:
    """
    Generate personalized workout notes based on user parameters.
    """
    # Base notes on readiness
    if readiness < 50:
        base_note = "Focus on recovery and mobility. Keep intensity low."
    elif readiness < 70:
        base_note = "Moderate training with focus on technique rather than intensity."
    else:
        base_note = "Good recovery status. Push intensity as planned."

    # Add type-specific notes
    if workout_type == "Strength":
        type_note = " Prioritize proper form and controlled movements."
    elif workout_type == "Conditioning":
        type_note = " Maintain consistent pacing throughout the session."
    else:  # Recovery
        type_note = " Focus on full range of motion and breathing techniques."

    # Add level-specific advice
    if fitness_level in ("Beginner", "Novice"):
        level_note = " Start with lighter weights to ensure proper technique."
    elif fitness_level == "Intermediate":
        level_note = " Progress weights when form is maintained for all reps."
    else:  # Advanced or Elite
        level_note = (
            " Incorporate advanced techniques like tempo changes and partial reps."
        )

    return base_note + type_note + level_note


# -------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
