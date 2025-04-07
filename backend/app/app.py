from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from config.db import get_all_checkins, get_workout_history, register_user, insert_check_in, user_exists, validate_date
from models.models import UserRegistration, DailyCheckIn
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=7)
jwt = JWTManager(app)
CORS(app, supports_credentials=True)


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
        return jsonify({"Unexcepted Error": f"Something went wrong {str(e)}"}), 400


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

        access_token = create_access_token(identity=str(data['id']),
                                           additional_claims=additional_claims
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


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)

