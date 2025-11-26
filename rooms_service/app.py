from flask import Flask, request, jsonify
import os
import redis
import json
import time

try:
    from models import db, Room
except ImportError:
    from rooms_service.models import db, Room



app = Flask(__name__)

db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# redis configuration
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
try:
    cache = redis.from_url(redis_url)
except Exception as e:
    print(f"Redis connection error: {e}")
    cache = None


db.init_app(app)

with app.app_context():
    db.create_all()


def invalidate_rooms_cache():
    """Helper to clear the rooms cache when data changes."""
    if cache:
        try:
            cache.delete('all_rooms')
            print("Room cache invalidated.")
        except redis.exceptions.ConnectionError:
            pass

@app.route('/rooms', methods=['POST'])
def create_room():
    """
    Creates a new meeting room.
    
    Expected JSON Input:
        - name (str)
        - capacity (int)
        - equipment (str)
        - location (str)

    :return: JSON message and status code 201.
    :rtype: tuple
    """
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
    # 1. GENERATE A UNIQUE CACHE KEY
    # We use request.full_path so that "/rooms?capacity=5" and "/rooms?capacity=10" 
    # are stored as different cache entries.
    cache_key = f"rooms_data_{request.full_path}"

    # 2. CHECK REDIS (The "Fast" Path)
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                # --- CACHE HIT ---
                print(f"CACHE HIT: Retrieved {cache_key} from Redis")
                # We return immediately. We DO NOT sleep.
                return jsonify(json.loads(cached_data)), 200
        except redis.exceptions.ConnectionError:
            print("⚠️ Redis unavailable, falling back to DB")

    # 3. DATABASE QUERY (The "Slow" Path)
    # If we are here, the data was NOT in Redis.
    print(f"CACHE MISS: Querying Database for {cache_key}")
    
    # --- SIMULATED LAG ---
    # We delay here to prove that the database is "slow" compared to Redis.
    time.sleep(2) 

    # Standard Filtering Logic
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

    # 4. STORE IN REDIS (Populate Cache)
    if cache:
        try:
            # Store the data for 60 seconds
            cache.setex(cache_key, 60, json.dumps(response_data))
        except redis.exceptions.ConnectionError:
            pass

    return jsonify(response_data), 200


@app.route('/rooms/<int:id>', methods=['PUT'])
def update_room(id):
    """Updates room details."""
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
    """Deletes a room by ID."""
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    
    invalidate_rooms_cache()
    
    return jsonify({"message": "Room deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)