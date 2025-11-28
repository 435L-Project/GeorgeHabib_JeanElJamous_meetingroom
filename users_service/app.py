from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests


try:
    from users_service.models import db, User
    from users_service.logger import audit_logger
    from users_service.crypto_utils import encrypt_data, decrypt_data
    from users_service.errors import register_error_handlers
except ImportError:
    from models import db, User
    from logger import audit_logger
    from crypto_utils import encrypt_data, decrypt_data
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
    db.create_all()

@app.route('/users/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
   
   
    encrypted_name = encrypt_data(data['full_name'])

    the_new_user = User(
        full_name=encrypted_name,
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        role=data['role']
    )
    db.session.add(the_new_user)
    db.session.commit()
    audit_logger.info(f"User registered: Username '{data['username']}' joined.")
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/users/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401

    audit_logger.info(f"User login: '{user.username}' authenticated successfully.")
    user_data = user.to_dict()
    user_data['full_name'] = decrypt_data(user.full_name)
    return jsonify({'message': 'Login successful', 'user': user_data}), 200

@app.route('/users/<username>', methods=['GET'])
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
   
    user_data = user.to_dict()
    user_data['full_name'] = decrypt_data(user.full_name)
    return jsonify(user_data), 200

@app.route('/users/<username>', methods=['PUT'])
def update_user(username):

    current_username = request.headers.get('X-User-Name')

    user_role = request.headers.get('X-User-Role')

    if user_role != 'admin' and current_username != username:
        return jsonify({'message': 'Unauthorized, you can only update your own profile'}), 403




    data = request.get_json()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if 'full_name' in data:
        user.full_name = encrypt_data(data['full_name'])
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    db.session.commit()
    audit_logger.info(f"User profile updated: account '{username} modified")
    return jsonify({'message': 'User updated successfully'}), 200

@app.route('/users/<username>', methods=['DELETE'])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    audit_logger.warning(f"User deleted: account '{username}' removed.")
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/users/<username>/bookings', methods=['GET'])
def get_user_bookings(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
   
    bookings_url = os.environ.get('BOOKINGS_API_URL', 'http://bookings_service:5003/bookings')
   
    try:
        response = requests.get(bookings_url)
        if response.status_code == 200:
            all_bookings = response.json()
            user_bookings = [b for b in all_bookings if b['user_id'] == user.id]
            return jsonify(user_bookings), 200
        else:
            return jsonify({'message': 'Failed to retrieve bookings'}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'Booking service unavailable'}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
