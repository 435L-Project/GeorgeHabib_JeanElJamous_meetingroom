from flask import Flask, request, jsonify
import os
import socket

app = Flask(__name__)


# Use 'db' if in Docker, 'localhost' if local
db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:password123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    from models import db, Room
    from logger import audit_logger
except ImportError:
    from users_service.models import db, Room
    from users_service.logger import audit_logger


db.init_app(app)

with app.app_context():
    db.create_all()

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
    data = request.get_json()
    new_room = Room(
        name=data['name'],
        capacity=data['capacity'],
        equipment=data['equipment'],
        location=data['location']
    )
    db.session.add(new_room)
    db.session.commit()

    # audit log
    audit_logger.info(f"Room created: '{new_room.name}' (ID: {new_room.id}, capacity: {new_room.capacity}) at {new_room.location}.")

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
    query = Room.query
    
    # Filter by Capacity
    capacity = request.args.get('capacity')
    if capacity:
        query = query.filter(Room.capacity >= int(capacity))
        
    # Filter by Location
    location = request.args.get('location')
    if location:
        query = query.filter(Room.location.ilike(f"%{location}%"))

    # Filter by Equipment
    equipment = request.args.get('equipment')
    if equipment:
        query = query.filter(Room.equipment.ilike(f"%{equipment}%"))
        
    rooms = Room.query.all()

    results = [room.to_dict() for room in rooms]
    response = {
            "server_id": socket.gethostname(), # This will print the Container ID
            "data": results
        }
    
    return jsonify(response), 200


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

    # audit log
    audit_logger.info(f"Room Updated: Room ID {id} details were modified.")

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
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()

    # audit log
    audit_logger.warning(f"Room Deleted: Room ID {id} was removed from inventory.")

    return jsonify({"message": "Room deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5002)