
import os
import json
import redis
from flask import Flask, request, jsonify

try:
    from rooms_service.models import db, Room

    try:
        from rooms_service.errors import register_error_handlers
    except ImportError:
        pass
except ImportError:
    from models import db, Room
    try:
        from errors import register_error_handlers
    except ImportError:
        pass

app = Flask(__name__)

db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
try:
    cache = redis.from_url(redis_url)
    cache.ping()
except Exception as e:
    print(f"Warning: Redis not connected: {e}")
    cache = None

db.init_app(app)


try:
    register_error_handlers(app)
except NameError:
    pass

with app.app_context():
    try:
        db.create_all()
    except:
        pass

def invalidate_rooms_cache():
    if cache:
        try:
            for key in cache.scan_iter("rooms_data_*"):
                cache.delete(key)
        except:
            pass



@app.route('/rooms', methods=['POST'])
def create_room():
    """
    Creates a new meeting room.

    Expected JSON input:
        - name (str): Name of the room
        - capacity (int): Maximum number of people in the room
        - equipment (str): Equipment available in the room
        - location (str): Location of the room

    :return: JSON message and status code 201
    :rtype: tuple
    """
    user_role = request.headers.get('X-User-Role')

    if user_role not in ['admin', 'facility_manager']:
        return jsonify({"error": "Unauthorized to create room: Only Admins or Facility Managers can add rooms"}), 403


    data = request.get_json()
    new_room = Room(
        name=data['name'],
        capacity=data['capacity'],
        equipment=data['equipment'],
        location=data['location']
    )
    db.session.add(new_room)
    db.session.commit()
    invalidate_rooms_cache()
    return jsonify({"message": "Room created successfully", "room": new_room.to_dict()}), 201

@app.route('/rooms', methods=['GET'])
def get_rooms():
    """
    Retrieves available rooms based on capacity, location, and equipment.

    Parameters:
        - capacity (int): Minimum capacity required.
        - location (str): Substring match for location.
        - equipment (str): Substring match for equipment.

    :return: List of room objects matching the criteria.
    :rtype: tuple
    """
    cache_key = f"rooms_data_{request.full_path}"
   
    # Check Redis
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data)), 200
        except:
            pass

    # Query DB
    query = Room.query
    capacity = request.args.get('capacity')
    if capacity:
        query = query.filter(Room.capacity >= int(capacity))
    location = request.args.get('location')
    if location:
        query = query.filter(Room.location.ilike(f"%{location}%"))
    equipment = request.args.get('equipment')
    if equipment:
        query = query.filter(Room.equipment.ilike(f"%{equipment}%"))
       
    rooms = query.all()
    response_data = [room.to_dict() for room in rooms]

    # Save to Redis
    if cache:
        try:
            cache.setex(cache_key, 60, json.dumps(response_data))
        except:
            pass
           
    return jsonify(response_data), 200

@app.route('/rooms/<int:id>', methods=['PUT'])
def update_room(id):
    """
    Updates room details (capacity, equipment).

    :param id: The ID of the room to update
    :type id: int
    :return: JSON message
    :rtype: tuple
    """
    room = Room.query.get_or_404(id)
    data = request.get_json()
    if 'capacity' in data:
        room.capacity = data['capacity']
    if 'equipment' in data:
        room.equipment = data['equipment']
    db.session.commit()
    invalidate_rooms_cache()
    return jsonify({"message": "Room updated successfully", "room": room.to_dict()}), 200

@app.route('/rooms/<int:id>', methods=['DELETE'])
def delete_room(id):
    """
    Deletes a room by ID.

    :param id: The ID of the room to delete
    :type id: int
    :return: JSON message
    :rtype: tuple
    """
    user_role = request.headers.get('X-User-Role')
    if not user_role or user_role.lower() != 'admin':
        return jsonify({"error": "Unauthorized to delete room"}), 403

    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    invalidate_rooms_cache()
    return jsonify({"message": "Room deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)