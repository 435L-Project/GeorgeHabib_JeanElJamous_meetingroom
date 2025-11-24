import pytest
from rooms_service.app import app, db, Room

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def cleanup_room(room_name):
    with app.app_context():
        room = Room.query.filter_by(name=room_name).first()
        if room:
            db.session.delete(room)
            db.session.commit()

def test_create_room(client):
    """Test API: Create a new room"""
    room_data = {
        "name": "Test Room A",
        "capacity": 10,
        "equipment": "Projector",
        "location": "Building 1"
    }
    cleanup_room("Test Room A")
    
    response = client.post('/rooms', json=room_data)
    assert response.status_code == 201
    assert response.json['room']['name'] == "Test Room A"

def test_get_rooms(client):

    room_data = {
        "name": "Test Room B",
        "capacity": 20,
        "equipment": "Whiteboard",
        "location": "Building 2"
    }
    cleanup_room("Test Room B")
    client.post('/rooms', json=room_data)

    response = client.get('/rooms?capacity=15')
    assert response.status_code == 200
    assert len(response.json) >= 1

    room_names = [r['name'] for r in response.json]
    assert "Test Room B" in room_names

def test_update_room(client):
    """Test API: Update room details"""
    room_data = {
        "name": "Test Room C",
        "capacity": 5,
        "equipment": "None",
        "location": "Building 3"
    }
    cleanup_room("Test Room C")
    create_resp = client.post('/rooms', json=room_data)
    room_id = create_resp.json['room']['id']

    update_data = {"capacity": 50}
    response = client.put(f'/rooms/{room_id}', json=update_data)
    assert response.status_code == 200
    assert response.json['room']['capacity'] == 50

def test_delete_room(client):
    """Test API: Delete a room"""
    room_data = {
        "name": "Test Room D",
        "capacity": 5,
        "equipment": "None",
        "location": "Building 4"
    }
    cleanup_room("Test Room D")
    create_resp = client.post('/rooms', json=room_data)
    room_id = create_resp.json['room']['id']

    response = client.delete(f'/rooms/{room_id}')
    assert response.status_code == 200
    
    with app.app_context():
        assert Room.query.get(room_id) is None