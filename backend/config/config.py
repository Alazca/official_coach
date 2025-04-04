import os
import datetime
from dotenv import load_dotenv

#  Load environments
BASEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv(os.path.join(BASEDIR,'.env'))

class Config:

# General settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Database settings
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'coach_db')

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
