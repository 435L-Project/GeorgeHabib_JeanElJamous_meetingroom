from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

try:
    from models import db, User
except ImportError:
    from users_service.models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:password123@localhost:5432/meeting_room_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# in this line, i am trying to initialize the database with the app
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/users/register', methods=['POST'])
def register():
    """Register a new user in the system.

    Expected JSON input:
        - full_name (str): Full name of the user
        - username (str): Unique username for the user
        - email (str): Email address of the user
        - password (str): Plain text password for the user account (will be hashed)
        - role (str): Role of the user

    :return: JSON response indicating success or failure of registration.
    :rtype: tuple    
    """

    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    the_new_user = User(
        full_name=data['full_name'],
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        role=data['role']
    )

    db.session.add(the_new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/users/login', methods=['POST'])
def login():
    """Authenticate a user and return their details.

    Expected JSON input:
        - username (str): Login username of the user
        - password (str): Login password of the user
    
    :return: JSON response containing the user object and success message.
    :rtype: tuple
    
    """

    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401

    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200


@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    """Retrieve user details by username.
    
    :param username: The unique username of the usre to retrieve
    :type username: str
    :return: JSON user object or error message
    :rtype: tuple  
    """

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@app.route('/users/<username>', methods=['PUT'])
def update_user(username):
    """Update user details by username.
    
    :param username: The username of the user to update
    :type username: str
    :return: JSON success message.
    :rtype: tuple
    """

    data = request.get_json()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    db.session.commit()

    return jsonify({'message': 'User updated successfully'}), 200


@app.route('/users/<username>', methods=['DELETE'])
def delete_user(username):
    """Permanently delete a user account from the database.
    
    :param username: The username of the account to delete.
    :type username: str
    :return: JSON success or error message.
    :rtype: tuple    
    """

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


@app.route('/users/<username>/bookings', methods=['GET'])
def get_user_bookings(username):
    """Retrieve the booking history for a specific user.
    
    :param username: The username to fetch bookings for.
    :type username: str
    :return: JSON list of bookings or error message.
    :rtype: tuple
    """

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    response = request.get('http://localhost:5003/bookings')

    if response.status_code == 200:
        all_bookings = response.json()
        user_bookings = [b for b in all_bookings if b['user_id'] == user.id]
        return jsonify(user_bookings), 200

    else:
        return jsonify({'message': 'Failed to retrieve bookings from Booking Service'}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5001)