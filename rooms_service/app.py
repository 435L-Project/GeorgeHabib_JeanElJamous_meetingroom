from flask import Flask, request, jsonify
from models import db, Room
import os

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# Currently set to SQLite for local testing.

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rooms.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/meeting_room_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/rooms', methods=['POST'])
def create_room():
    """
    Creates a new meeting room.
    :return: JSON message and status code 201
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
    return jsonify({"message": "Room created successfully", "room": new_room.to_dict()}), 201

@app.route('/rooms', methods=['GET'])
def get_rooms():
    """
    Retrieves all rooms, with optional filtering.
    :param capacity: (Query Param) Filter by minimum capacity
    :return: JSON list of rooms
    """
    capacity_filter = request.args.get('capacity')
    if capacity_filter:
        rooms = Room.query.filter(Room.capacity >= int(capacity_filter)).all()
    else:
        rooms = Room.query.all()
    return jsonify([room.to_dict() for room in rooms]), 200

@app.route('/rooms/<int:id>', methods=['PUT'])
def update_room(id):
    """
    Updates room details (capacity, equipment).
    :param id: The ID of the room to update
    :return: JSON message
    """
    room = Room.query.get_or_404(id)
    data = request.get_json()
    if 'capacity' in data:
        room.capacity = data['capacity']
    if 'equipment' in data:
        room.equipment = data['equipment']
    db.session.commit()
    return jsonify({"message": "Room updated successfully", "room": room.to_dict()}), 200

@app.route('/rooms/<int:id>', methods=['DELETE'])
def delete_room(id):
    """
    Deletes a room by ID.
    :param id: The ID of the room to delete
    :return: JSON message
    """
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({"message": "Room deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5002)