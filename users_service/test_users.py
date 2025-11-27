import pytest
from app import app, db, User
from crypto_utils import decrypt_data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def get_test_user_data():
    return {
        "full_name": "Test User",
        "username": "pytest_user",
        "email": "testpy@aub.edu.lb",
        "password": "testpassword",
        "role": "Student"
    }

def clean_up_db():
    with app.app_context():
        user = User.query.filter_by(username="pytest_user").first()
        if user:
            db.session.delete(user)
            db.session.commit()


def test_register_user(client):
    """Test user registration endpoint."""
    clean_up_db()

    user_data = get_test_user_data()
    response = client.post('/users/register', json=user_data)
    assert response.status_code == 201
    assert b"User registered successfully" in response.data

def test_login_user(client):
    """Test user login endpoint."""
    clean_up_db()

    user_data = get_test_user_data()

    # Ensure the user is registered first
    client.post('/users/register', json=user_data)

    login_data = {
        "username": user_data['username'],
        "password": user_data['password']
    }
    response = client.post('/users/login', json=login_data)
    assert response.status_code == 200
    assert b"Login successful" in response.data

def test_get_user(client):
    """Test API: Get user profile"""

    clean_up_db()
    user_data = get_test_user_data()
    client.post('/users/register', json=user_data)

    response = client.get(f'/users/{user_data["username"]}')
    assert response.status_code ==200
    assert user_data['email'] in response.json['email']


def test_update_user(client):
    """ Test API: Update user details"""

    clean_up_db()
    user_data = get_test_user_data()
    client.post('/users/register', json=user_data)

    update_payload = {"full_name": "Updated Name"}
    response = client.put(f'/users/{user_data["username"]}', json=update_payload)
    assert response.status_code ==200

    get_resp = client.get(f'/users/{user_data["username"]}')
    encrypted_name = get_resp.json['full_name']
    decrypted_name = decrypt_data(encrypted_name)
    
    assert decrypted_name == "Updated Name"


def test_delete_user(client):
    """Test API: Delete user"""

    clean_up_db()
    user_data = get_test_user_data()
    client.post('/users/register', json=user_data)

    response = client.delete(f'/users/{user_data["username"]}')
    assert response.status_code ==200

    get_resp = client.get(f'/users/{user_data["username"]}')
    assert get_resp.status_code == 404