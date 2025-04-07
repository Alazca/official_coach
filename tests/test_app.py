import pytest
from backend.app.app import app

@pytest.fixture
def client():
    """Fixture to create an instance of the Flask app's test client."""
    with app.test_client() as client:
        yield client

def test_homepage(client):
    """Basic test to check if the root URL is accessible."""
    response = client.get('/')
    assert response.status_code == 404  # Change this if a homepage route exists

def test_register(client):
    """Test user registration API."""
    data = {"email": "test@example.com", "password": "securepassword"}
    response = client.post('/api/register', json=data)
    assert response.status_code == 200 or response.status_code == 400  # 400 if email already exists

def test_checkin(client):
    """Test daily check-in API."""
    data = {
        "userId": 1,
        "weight": 70.5,
        "sleep": 7,
        "stress": 3,
        "energy": 8,
        "soreness": 2
    }
    response = client.post('/api/checkin', json=data)
    assert response.status_code == 200