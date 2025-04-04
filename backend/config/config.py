import os
from dotenv import load_dotenv
import datetime

class Config:
# Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
    os.makedirs(db_dir, exist_ok=True)

# Configure SQLite database
    db_path = os.path.join(db_dir, 'coach.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)


