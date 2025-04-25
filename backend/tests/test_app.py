# tests/test_app.py
import pytest
from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    with app.test_client() as client:
        yield client


def test_register_success(client):
    response = client.post(
        "/api/register",
        json={
            "email": "test11@example.com",
            "password": "Secret123!",
            "name": "Test User",
            "gender": "Female",
            "dob": "2000-01-01",
            "height": 160.0,
            "weight": 60.0,
            "initialActivityLevel": "Moderate",
        },
    )

    print("RESPONSE JSON:", response.get_json())
    assert response.status_code == 200  # a 200 OK response
    assert "Successfully registered user" in response.get_json().get("message", "")


def test_register_missing_fields(client):
    response = client.post(
        "/api/register",
        json={
            "email": "missing@example.com",
            "password": "Secret123!",
            # missing name, gender, dob, height, weight, initialActivityLevel
        },
    )
    assert response.status_code == 400
    assert "Validation error" in response.get_json()


def test_register_duplicate_email(client):
    valid_data = {
        "email": "duplicate@example.com",
        "password": "Secret123!",
        "name": "Dup User",
        "gender": "Male",
        "dob": "1995-05-05",
        "height": 170.0,
        "weight": 65.0,
        "initialActivityLevel": "Active",
    }
    client.post("/api/register", json=valid_data)  # first time should work
    response = client.post("/api/register", json=valid_data)  # duplicate
    assert response.status_code == 400
    assert "Database error" in response.get_json()


def test_login_success(client):
    # Register first
    client.post(
        "/api/register",
        json={
            "email": "loginuser@example.com",
            "password": "Secret123!",
            "name": "Login User",
            "gender": "Female",
            "dob": "2001-10-10",
            "height": 160.0,
            "weight": 55.0,
            "initialActivityLevel": "Moderate",
        },
    )
    # Now log in
    response = client.post(
        "/api/login", json={"email": "loginuser@example.com", "password": "Secret123!"}
    )
    assert response.status_code == 200
    assert "access token" in response.get_json()


def test_login_wrong_password(client):
    # Register first
    client.post(
        "/api/register",
        json={
            "email": "wrongpass@example.com",
            "password": "Secret123!",
            "name": "Wrong Pass",
            "gender": "Other",
            "dob": "2002-02-02",
            "height": 165.0,
            "weight": 60.0,
            "initialActivityLevel": "Casual",
        },
    )
    # Try with wrong password
    response = client.post(
        "/api/login",
        json={"email": "wrongpass@example.com", "password": "Wrong123!"},  # incorrect
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.get_json().get("error", "")


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/login", json={"email": "ghost@example.com", "password": "DoesntMatter123"}
    )
    assert response.status_code == 404
    assert "User does not exist" in response.get_json().get("error", "")


def test_get_current_user(client):
    # First, register and log in a user to get the JWT
    client.post(
        "/api/register",
        json={
            "email": "me@example.com",
            "password": "Secret123!",
            "name": "Me Myself",
            "gender": "Other",
            "dob": "1990-01-01",
            "height": 170.0,
            "weight": 65.0,
            "initialActivityLevel": "Casual",
        },
    )

    login_resp = client.post(
        "/api/login", json={"email": "me@example.com", "password": "Secret123!"}
    )
    access_token = login_resp.get_json()["access token"]

    # Now access the protected /api/me route
    me_resp = client.get("/api/me", headers={"Authorization": f"Bearer {access_token}"})

    assert me_resp.status_code == 200
    data = me_resp.get_json()
    assert data["email"] == "me@example.com"
    assert "user_id" in data


def test_checkin_success(client):
    # Register and log in to get a token
    client.post(
        "/api/register",
        json={
            "email": "checkin@example.com",
            "password": "Secret123!",
            "name": "Checker",
            "gender": "Female",
            "dob": "1999-09-09",
            "height": 165.0,
            "weight": 60.0,
            "initialActivityLevel": "Moderate",
        },
    )

    login_resp = client.post(
        "/api/login", json={"email": "checkin@example.com", "password": "Secret123!"}
    )
    token = login_resp.get_json()["access token"]

    # Submit a check-in with the token
    checkin_resp = client.post(
        "/api/checkin",
        headers={"Authorization": f"Bearer {token}"},
        json={"weight": 61.5, "sleep": 7, "stress": 3, "energy": 4, "soreness": 1},
    )

    assert checkin_resp.status_code == 200
    assert checkin_resp.get_json()["message"] == "Check-in saved successfully"


def test_get_checkins_success(client):
    # Register and log in a user
    client.post(
        "/api/register",
        json={
            "email": "history@example.com",
            "password": "Secret123!",
            "name": "Hist User",
            "gender": "Female",
            "dob": "1997-07-07",
            "height": 162.0,
            "weight": 59.0,
            "initialActivityLevel": "Casual",
        },
    )

    login_resp = client.post(
        "/api/login", json={"email": "history@example.com", "password": "Secret123!"}
    )
    token = login_resp.get_json()["access token"]

    # Submit a check-in
    client.post(
        "/api/checkin",
        headers={"Authorization": f"Bearer {token}"},
        json={"weight": 59.2, "sleep": 7, "stress": 2, "energy": 3, "soreness": 1},
    )

    # Get user ID from /api/me
    me_resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me_resp.get_json()["user_id"]

    # Now fetch check-ins
    history_resp = client.get(
        f"/api/checkins/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )

    assert history_resp.status_code == 200
    data = history_resp.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_nutrition_success(client):
    # Register & login
    client.post(
        "/api/register",
        json={
            "email": "nutrition@example.com",
            "password": "Secret123!",
            "name": "Nutri Tester",
            "gender": "Female",
            "dob": "1996-06-06",
            "height": 160.0,
            "weight": 58.0,
            "initialActivityLevel": "Moderate",
        },
    )
    login_resp = client.post(
        "/api/login", json={"email": "nutrition@example.com", "password": "Secret123!"}
    )
    token = login_resp.get_json()["access token"]

    # Call the route
    response = client.get(
        "/api/nutrition", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_workout_history_success(client):
    # Register and log in a user
    client.post(
        "/api/register",
        json={
            "email": "workout@example.com",
            "password": "Secret123!",
            "name": "Workout Tester",
            "gender": "Male",
            "dob": "1990-01-01",
            "height": 175.0,
            "weight": 70.0,
            "initialActivityLevel": "Active",
        },
    )
    login_resp = client.post(
        "/api/login", json={"email": "workout@example.com", "password": "Secret123!"}
    )
    token = login_resp.get_json()["access token"]

    # Get workout history (even if none exist yet)
    response = client.get(
        "/api/workout-history", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
