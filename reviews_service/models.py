from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Review(db.Model):
    """
    Represents a user review for a specific room

    :param id: Unique identifier for the review.
    :type id: int
    :param user_id: ID of the user who wrote the review.
    :type user_username: int
    :param room_id: ID of the room being reviewed.
    :type room_id: int
    :param rating: Rating given by the user (1-5).
    :type rating: int
    :param comment: Comment provided by the user.
    :type comment: str
    :param timestamp: Date and time when the review was created.
    :type timestamp: datetime
    :param is_flagged: Moderation status.
    :type is_flagged: bool   
    """
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    is_flagged = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """
        Converts the Review object to a dictionary.

        :return: Dictionary representation of the Review object.
        :rtype: dict
        """
        return {
            'id': self.id,
            'user_username': self.user_username,
            'room_id': self.room_id,
            'rating': self.rating,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat(),
            'is_flagged': self.is_flagged
        }