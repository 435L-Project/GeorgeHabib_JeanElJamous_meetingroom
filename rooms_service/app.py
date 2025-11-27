import os
import json
import redis
from flask import Flask, request, jsonify
from rooms_service.models import db, Room

app = Flask(__name__)

# --- CONFIGURATION ---
db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- REDIS SETUP (From Caching Task) ---
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
try:
    cache = redis.from_url(redis_url)
    cache.ping() # Check connection
except Exception as e:
    print(f"Warning: Redis not connected: {e}")
    cache = None

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
    except:
        pass

# --- CACHE HELPER ---
def invalidate_rooms_cache():
    if cache:
        try:
            for key in cache.scan_iter("rooms_data_*"):
                cache.delete(key)
        except:
            pass

@app.route('/rooms', methods=['POST'])
def create_room():
    data = request.get_json()
    new_room = Room(
        name=data['name'],
        capacity=data['capacity'],
        equipment=data['equipment'],
        location=data['location']
    )
    db.session.add(new_room)
    db.session.commit()
    
    # Invalidate cache on update
    invalidate_rooms_cache()
    
    return jsonify({"message": "Room created successfully", "room": new_room.to_dict()}), 201

@app.route('/rooms', methods=['GET'])
def get_rooms():
    # 1. GENERATE CACHE KEY
    cache_key = f"rooms_data_{request.full_path}"

    # 2. CHECK REDIS (Fast Path)
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                # We return directly (Fast!)
                return jsonify(json.loads(cached_data)), 200
        except:
            pass

    # 3. DATABASE QUERY (Standard Path)

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

    # 4. STORE IN REDIS
    if cache:
        try:
            cache.setex(cache_key, 60, json.dumps(response_data))
        except:
            pass

    return jsonify(response_data), 200

@app.route('/rooms/<int:id>', methods=['PUT'])
def update_room(id):
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
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    
    invalidate_rooms_cache()
    
    return jsonify({"message": "Room deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)