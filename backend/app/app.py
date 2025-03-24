from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

# Create Flask application
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Ensure database directory exists
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
os.makedirs(db_dir, exist_ok=True)

# Configure SQLite database
db_path = os.path.join(db_dir, 'coach.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class DailyCheckin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float)
    sleep_quality = db.Column(db.Integer)
    stress_level = db.Column(db.Integer)
    energy_level = db.Column(db.Integer)
    soreness_level = db.Column(db.Integer)
    readiness_score = db.Column(db.Integer)
    check_in_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
        
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'})

@app.route('/api/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    
    checkin = DailyCheckin(
        user_id=data['userId'],
        weight=data['weight'],
        sleep_quality=data['sleep'],
        stress_level=data['stress'],
        energy_level=data['energy'],
        soreness_level=data['soreness'],
        check_in_date=datetime.datetime.now().date()
    )
    
    db.session.add(checkin)
    db.session.commit()
    
    return jsonify({'message': 'Check-in recorded successfully'})

@app.route('/api/checkins/<int:user_id>')
def get_checkins(user_id):
    checkins = DailyCheckin.query.filter_by(user_id=user_id).order_by(DailyCheckin.check_in_date.desc()).all()
    return jsonify([{
        'id': c.id,
        'weight': c.weight,
        'sleep_quality': c.sleep_quality,
        'stress_level': c.stress_level,
        'energy_level': c.energy_level,
        'soreness_level': c.soreness_level,
        'readiness_score': c.readiness_score,
        'check_in_date': c.check_in_date.isoformat(),
    } for c in checkins])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
