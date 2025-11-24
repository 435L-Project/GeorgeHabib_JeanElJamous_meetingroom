import pytest
from datetime import datetime, timedelta
from bookings_service.app import app, db, Booking

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_create_booking(client):
    start_time = datetime(2026, 1, 1, 10, 0, 0)
    end_time = datetime(2026, 1, 1, 11, 0, 0)
    
    booking_data = {
        "user_id": 1,
        "room_id": 999, 
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    

    with app.app_context():
        existing = Booking.query.filter_by(room_id=999).delete()
        db.session.commit()

    response = client.post('/bookings', json=booking_data)
    assert response.status_code == 201


    response_conflict = client.post('/bookings', json=booking_data)
    assert response_conflict.status_code == 409
    assert "already booked" in response_conflict.json['error']

def test_get_bookings(client):

    response = client.get('/bookings')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_check_availability(client):

    check_data = {
        "room_id": 999,
        "start_time": "2030-01-01T10:00:00",
        "end_time": "2030-01-01T11:00:00"
    }

    with app.app_context():
        Booking.query.filter_by(room_id=999, start_time=datetime(2030, 1, 1, 10, 0, 0)).delete()
        db.session.commit()

    response = client.post('/bookings/check', json=check_data)
    assert response.status_code == 200
    assert response.json['available'] == True

def test_cancel_booking(client):
    start_time = datetime(2026, 2, 1, 10, 0, 0)
    end_time = datetime(2026, 2, 1, 11, 0, 0)
    
    booking_data = {
        "user_id": 1,
        "room_id": 888,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    create_resp = client.post('/bookings', json=booking_data)
    booking_id = create_resp.json['booking']['id']

    response = client.delete(f'/bookings/cancel/{booking_id}')
    assert response.status_code == 200
    assert "cancelled" in response.json['message']
