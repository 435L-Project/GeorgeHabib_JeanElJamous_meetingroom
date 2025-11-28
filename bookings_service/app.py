import os
from flask import Flask, request, jsonify
from datetime import datetime
from sqlalchemy import func

try:
    from bookings_service.models import db, Booking
    from bookings_service.logger import audit_logger
    try:
        from bookings_service.errors import register_error_handlers
    except ImportError:
        pass
except ImportError:
    from models import db, Booking
    from logger import audit_logger
    try:
        from errors import register_error_handlers
    except ImportError:
        pass

app = Flask(__name__)

db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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


@app.route('/api/v1/analytics', methods=['GET'])
def get_booking_analytics():
    """Returns aggregated statistics about bookings.
    
    :return: JSON with total bookings, most popular room, and its booking count.
    :rtype: tuple
    """
    total_bookings = db.session.query(func.count(Booking.id)).scalar()
   
    popular_room = db.session.query(
        Booking.room_id, func.count(Booking.room_id)
    ).group_by(Booking.room_id).order_by(func.count(Booking.room_id).desc()).first()

    stats = {
        "total_bookings_count": total_bookings,
        "most_popular_room_id": popular_room[0] if popular_room else None,
        "bookings_for_popular_room": popular_room[1] if popular_room else 0
    }
    return jsonify(stats), 200



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
   
    # Conflict Logic
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

    # Log the audit event
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
    current_user_id = request.headers.get('X-User-ID')

    booking = Booking.query.get_or_404(id)
    if str(booking.user_id) != str(current_user_id):
        return jsonify({"error": "Unauthorized to cancel this booking"}), 403
    db.session.delete(booking)
    db.session.commit()
   
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