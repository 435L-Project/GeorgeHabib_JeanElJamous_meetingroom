from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Use 'db' if in Docker, 'localhost' if local
db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:password123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    from models import db, Booking
    from logger import audit_logger
except ImportError:
    from bookings_service.models import db, Booking
    from bookings_service.logger import audit_logger


db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/bookings', methods=['POST'])
def create_booking():
    """
    Creates a booking if the room is available.
    checks for time conflicts before saving.

    Expected JSON input:
        - user_id (int)
        - room_id (int)
        - start_time (str): ISO format datetime string
        - end_time (str): ISO format datetime string

    :return: JSON success message or 409 conflict error.
    :rtype: tuple
    """
    data = request.get_json()
    room_id = data['room_id']
    start = datetime.fromisoformat(data['start_time'])
    end = datetime.fromisoformat(data['end_time'])
    
    conflict = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.end_time > start,
        Booking.start_time < end
    ).first()
    
    if conflict:
        return jsonify({"error": "Room is already booked for this time slot"}), 409
        
    new_booking = Booking(
        user_id=data['user_id'],
        room_id=room_id,
        start_time=start,
        end_time=end
    )
    db.session.add(new_booking)
    db.session.commit()

    # audit log
    audit_logger.info(f"Booking Created: User {data['user_id']} reserved Room {room_id} from {start} to {end}.")


    return jsonify({"message": "Booking successful", "booking": new_booking.to_dict()}), 201

@app.route('/bookings', methods=['GET'])
def get_bookings():
    """Retrieves all bookings.
    
    :return: List of all bookings.
    :rtype: tuple    
    """
    bookings = Booking.query.all()
    return jsonify([b.to_dict() for b in bookings]), 200

@app.route('/bookings/cancel/<int:id>', methods=['DELETE'])
def cancel_booking(id):
    """Cancels (deletes) a booking by ID.
    
    :param id: ID of the booking to cancel.
    :type id: int
    :return: JSON success message.
    :rtype: tuple
    """
    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()

    # audit log
    audit_logger.warning(f"Booking Cancelled: Reservation ID {id} was cancelled.")

    return jsonify({"message": "Booking cancelled"}), 200


@app.route('/bookings/check', methods=['POST'])
def check_availability():
    """
    Checks if a room is available for a specific time slot.

    Expected JSON input:
        - room_id (int)
        - start_time (str)
        - end_time (str)

    :return: JSON availability status.
    :rtype: tuple
    """
    data = request.get_json()
    room_id = data['room_id']
    start = datetime.fromisoformat(data['start_time'])
    end = datetime.fromisoformat(data['end_time'])
    
    conflict = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.end_time > start,
        Booking.start_time < end
    ).first()
    
    if conflict:
        return jsonify({"available": False, "message": "Room is occupied"}), 200
    else:
        return jsonify({"available": True, "message": "Room is available"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5003)