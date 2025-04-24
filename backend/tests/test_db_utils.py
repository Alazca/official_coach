# test API calls instead

import pytest
import sqlite3
import datetime
# from backend.database.db import (
#     get_user_data,
#     get_latest_checkin,
#     save_readiness_score,
#     update_checkin_with_readiness,
#     get_all_checkins
# )
from backend.config.config import Config


# Fixture to set up a test database
@pytest.fixture
def test_db():
    # Create an in-memory database for testing
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create test tables
    cursor.executescript('''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            gender TEXT,
            dateOfBirth DATE,
            height REAL,
            weight REAL,
            initialActivityLevel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE daily_checkins (
            checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            weight REAL,
            sleep_quality INTEGER,
            stress_level INTEGER,
            energy_level INTEGER,
            soreness_level INTEGER,
            readiness_id INTEGER,
            check_in_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE readiness_scores (
            readiness_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            readiness_score INTEGER,
            contributing_factors TEXT,
            readiness_date DATE NOT NULL,
            source TEXT,
            alignment_score REAL,
            overtraining_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Insert test data
    cursor.execute('''
        INSERT INTO users (
            user_id, email, password_hash, name, gender, dateOfBirth, height, weight, initialActivityLevel
        ) VALUES (
            1, 'test@example.com', 'hash123', 'Test User', 'Male', '1990-01-01', 180, 75, 'Moderate'
        )
    ''')
    
    # Insert test check-ins
    cursor.execute('''
        INSERT INTO daily_checkins (
            checkin_id, user_id, weight, sleep_quality, stress_level, energy_level, soreness_level, check_in_date
        ) VALUES (
            1, 1, 75, 8, 3, 7, 4, '2025-04-15'
        )
    ''')
    
    cursor.execute('''
        INSERT INTO daily_checkins (
            checkin_id, user_id, weight, sleep_quality, stress_level, energy_level, soreness_level, check_in_date
        ) VALUES (
            2, 1, 74.5, 7, 4, 6, 5, '2025-04-16'
        )
    ''')
    
    conn.commit()
    
    # Return the connection
    yield conn
    
    # Close the connection after tests
    conn.close()


# Mock Config class to use the test database
class MockConfig(Config):
    def get_database_path(self):
        return ':memory:'


# Test get_user_data
def test_get_user_data(test_db, monkeypatch):
    # Mock the Config to use our test DB
    monkeypatch.setattr('backend.utils.db_utils.Config', MockConfig)
    
    # Test the function
    user = get_user_data(1)
    
    # Assertions
    assert user is not None
    assert user['email'] == 'test@example.com'
    assert user['name'] == 'Test User'
    
    # Test non-existent user
    non_existent = get_user_data(999)
    assert non_existent is None


# Test get_latest_checkin
def test_get_latest_checkin(test_db, monkeypatch):
    # Mock the Config to use our test DB
    monkeypatch.setattr('backend.utils.db_utils.Config', MockConfig)
    
    # Test the function
    checkin = get_latest_checkin(1)
    
    # Assertions
    assert checkin is not None
    assert checkin['checkin_id'] == 2  # The most recent one
    assert checkin['check_in_date'] == '2025-04-16'
    
    # Test for user with no check-ins
    no_checkins = get_latest_checkin(999)
    assert no_checkins is None


# Test save_readiness_score and update_checkin_with_readiness
def test_readiness_flow(test_db, monkeypatch):
    # Mock the Config to use our test DB
    monkeypatch.setattr('backend.utils.db_utils.Config', MockConfig)
    
    # Test save_readiness_score
    readiness_data = {
        "user_id": 1,
        "readiness_score": 85,
        "contributing_factors": "Sleep: 8, Stress: 3",
        "readiness_date": "2025-04-16",
        "source": "Auto",
        "alignment_score": 0.8,
        "overtraining_score": 0.2
    }
    
    readiness_id = save_readiness_score(readiness_data)
    assert isinstance(readiness_id, int)
    assert readiness_id > 0
    
    # Test update_checkin_with_readiness
    result = update_checkin_with_readiness(2, readiness_id)
    assert result is True
    
    # Verify the update worked
    cursor = test_db.cursor()
    cursor.execute("SELECT readiness_id FROM daily_checkins WHERE checkin_id = 2")
    updated_checkin = cursor.fetchone()
    assert updated_checkin['readiness_id'] == readiness_id


# Test get_all_checkins
def test_get_all_checkins(test_db, monkeypatch):
    # Mock the Config to use our test DB
    monkeypatch.setattr('backend.utils.db_utils.Config', MockConfig)
    
    # Test without date filters
    checkins = get_all_checkins(1)
    assert len(checkins) == 2
    
    # Test with date filters
    filtered_checkins = get_all_checkins(1, start_date='2025-04-16', end_date='2025-04-16')
    assert len(filtered_checkins) == 1
    assert filtered_checkins[0]['check_in_date'] == '2025-04-16'
    
    # Test with non-existent user
    no_checkins = get_all_checkins(999)
    assert len(no_checkins) == 0

