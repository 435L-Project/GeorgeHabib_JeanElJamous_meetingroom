from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """
    Represents a user in the system.

    :param id: Unique identifier for the user.
    :type id: int
    :param full_name: Full name of the user.
    :type full_name: str
    :param username: Unique username for the user.
    :type username: str
    :param email: Unique email address of the user.
    :type email: str
    :param password: Hashed password for the user.
    :type password: str
    :param role: Role of the user (e.g., admin, user).
    :type role: str
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(300), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), nullable=False)

    def to_dict(self):
        """
        Converts the User object to a dictionary.
        
        :return: Dictionary representation of the User object.
        :rtype: dict
        """
        return {
            'id': self.id,
            'full_name': self.full_name,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }