import pytest
from engines.alignment_matrix import evaluate_vectors
from config.db import register_user

@pytest.fixture
def full_user_checkin():
    return {
        "profile": {
            "email": "testuser@example.com",
            "password": "Test@1234",
            "name": "Test User",
            "gender": "Male",
            "dob": "1990-01-01",
            "height": 175,
            "weight": 70,
            "initialActivityLevel": "Moderate"
        },
        "checkin": {
            "protein": 120,
            "calories": 2200,
            "carbs": 250,
            "fats": 60,
            "sleep_quality": 7,
            "stress_level": 4,
            "soreness": 3,
            "readiness": 8
        }
    }

def test_vector_evaluation_for_registered_user(full_user_checkin):
    # Register the user
    user_info = full_user_checkin["profile"]
    user_id = register_user(
        user_info["email"],
        user_info["password"],
        user_info["name"],
        user_info["gender"],
        user_info["dob"],
        user_info["height"],
        user_info["weight"],
        user_info["initialActivityLevel"]
    )
    assert isinstance(user_id, int)

    # Run vector evaluation
    result = evaluate_vectors(full_user_checkin["checkin"], user_id)

    assert "goal_alignment" in result
    assert "overtraining_risk" in result
    assert "recommendation" in result
