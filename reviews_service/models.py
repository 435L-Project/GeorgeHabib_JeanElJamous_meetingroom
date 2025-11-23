from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_username = db.Column(db.String(50), nullable=False)
    room_id = db.Column(db.Integer, nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    is_flagged = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_username': self.user_username,
            'room_id': self.room_id,
            'rating': self.rating,
            'comment': self.comment,
            'timestamp': self.timestamp.isoformat(),
            'is_flagged': self.is_flagged
        }