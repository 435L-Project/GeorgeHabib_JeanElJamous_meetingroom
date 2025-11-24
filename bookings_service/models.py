from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Booking(db.Model):
    """
    Represents a booking reservation for a room.

    :param id: Unique identifier for the booking.
    :type id: int
    :param user_id: ID of the user who made the booking.
    :type user_id: int
    :param room_id: ID of the room being booked.
    :type room_id: int
    :param start_time: Start date and time of the booking.
    :type start_time: datetime
    :param end_time: End date and time of the booking.
    :type end_time: datetime
    """
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        """
        Converts the Booking object to a dictionary.
        
        :return: Dictionary representation of the Booking object.
        :rtype: dict
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }