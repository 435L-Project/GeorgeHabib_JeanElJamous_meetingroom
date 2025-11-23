from flask import Flask, request, jsonify
from models import db, Booking
from datetime import datetime

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# Currently set to SQLite for local testing.

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/meeting_room_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/bookings', methods=['POST'])
def create_booking():
    """
    Creates a booking if the room is available.
    checks for time conflicts before saving.
    """
    data = request.get_json()
    room_id = data['room_id']
    start = datetime.fromisoformat(data['start_time'])
    end = datetime.fromisoformat(data['end_time'])
    
    # CONFLICT LOGIC: Check if any booking overlaps with requested time
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
    return jsonify({"message": "Booking successful", "booking": new_booking.to_dict()}), 201

@app.route('/bookings', methods=['GET'])
def get_bookings():
    """Retrieves all bookings."""
    bookings = Booking.query.all()
    return jsonify([b.to_dict() for b in bookings]), 200

@app.route('/bookings/cancel/<int:id>', methods=['POST'])
def cancel_booking(id):
    """Cancels a booking by ID."""
    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    return jsonify({"message": "Booking cancelled"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5003)