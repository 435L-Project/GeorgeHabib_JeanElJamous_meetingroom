from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Room(db.Model):
    """
    Represents a meeting room in the system.

    :param id: Unique identifier for the room.
    :type id: int
    :param name: Name of the room.
    :type name: str
    :param capacity: Maximum number of people in the room.
    :type capacity: int
    :param equipment: Equipment available in the room.
    :type equipment: str
    :param location: Location of the room.
    :type location: str    
    """
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False,index=True)
    equipment = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=False,index=True)

    def to_dict(self):
        """
        Converts the Room object to a dictionary.

        :return: Dictionary representation of the Room object.
        :rtype: dict
        """
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "equipment": self.equipment,
            "location": self.location
        }