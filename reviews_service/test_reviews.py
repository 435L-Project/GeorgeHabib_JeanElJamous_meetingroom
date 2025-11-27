import pytest
from reviews_service.app import app, db, Review

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def random_review(client):
    review_data = {
        "user_id": 99,
        "room_id": 999,
        "rating": 5,
        "comment": "Nice room"
    }
    client.post('/reviews', json=review_data)
    
    # Get the review from DB to find its ID
    with app.app_context():
        review = Review.query.filter_by(user_id=99).order_by(Review.id.desc()).first()
        return review.id

def test_submit_review(client):
    """Test API: Submit a review"""
    data = {
        "user_id": 1,
        "room_id": 101,
        "rating": 4,
        "comment": "Great!"
    }
    response = client.post('/reviews', json=data)
    assert response.status_code == 201

def test_sanitization(client):
    """Test API: Check if scripts are cleaned"""
    data = {
        "user_id": 2,
        "room_id": 102,
        "rating": 1,
        "comment": "<script>alert('bad')</script>"
    }
    client.post('/reviews', json=data)
    
    response = client.get('/reviews/room/102')
    assert b"<script>" not in response.data

def test_moderation_flag(client, random_review):
    """Test API: Flag a review"""
    review_id = random_review
    payload = {"action": "flag"}
    
    response = client.post(f'/reviews/moderate/{review_id}', json=payload)
    assert response.status_code == 200
    
    with app.app_context():
        r = Review.query.get(review_id)
        assert r.is_flagged == True

def test_delete_review(client, random_review):
    """Test API: Delete a review"""
    review_id = random_review
    response = client.delete(f'/reviews/{review_id}')
    assert response.status_code == 200