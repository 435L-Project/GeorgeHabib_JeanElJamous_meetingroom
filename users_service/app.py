from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:password123@localhost:5432/meeting_room_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# in this line, i am trying to initialize the database with the app
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/users/register', methods=['POST'])
def register():
    """Register a new user. (should do the correct sphinx documentation)"""

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
    """Authenticate a user and return their details."""

    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401

    return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200


@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    """Retrieve user details by username."""

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@app.route('/users/<username>', methods=['PUT'])
def update_user(username):
    """Update user details by username."""

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
    """Delete a user by username."""

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


@app.route('/users/<username>/bookings', methods=['GET'])
def get_user_bookings(username):
    """Retrieve all bookings for a specific user from the bookings service."""

    user = User.query.filter_by(username=username).first()

    # TODO: IMPLEMENT  inter-service communicaiton to Bookings service

    return jsonify({'message': 'Booking history retrieval to be implemented with Service 3'}), 200



if __name__ == '__main__':
    app.run(debug=True, port=5001)