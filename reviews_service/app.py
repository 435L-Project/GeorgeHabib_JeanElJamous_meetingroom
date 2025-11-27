import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import bleach

# --- 1. Imports (Docker Compatible) ---
try:
    from reviews_service.models import db, Review
    from reviews_service.logger import audit_logger
    # Try importing errors if the file exists
    try:
        from reviews_service.errors import register_error_handlers
    except ImportError:
        pass
except ImportError:
    from models import db, Review
    from logger import audit_logger
    try:
        from errors import register_error_handlers
    except ImportError:
        pass

app = Flask(__name__)

# --- 2. Configuration ---
# Use Postgres for Docker
db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Register error handlers if available
try:
    register_error_handlers(app)
except NameError:
    pass

with app.app_context():
    try:
        db.create_all()
    except:
        pass

# --- 3. New Analytics Endpoint (Task 5) ---
@app.route('/api/v1/analytics', methods=['GET'])
def get_review_analytics():
    """Returns aggregated statistics about reviews."""
    avg_rating = db.session.query(func.avg(Review.rating)).scalar()
    total_reviews = db.session.query(func.count(Review.id)).scalar()
   
    stats = {
        "global_average_rating": round(float(avg_rating), 2) if avg_rating else 0,
        "total_reviews_submitted": total_reviews
    }
    return jsonify(stats), 200

# --- 4. Standard Routes (Merged Logic) ---

@app.route('/reviews', methods=['POST'])
def submit_review():
    """Submit a new review for a meeting room."""
    data = request.get_json()

    if not (1 <= data['rating'] <= 5):
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400
   
    cleaned_comment = bleach.clean(data['comment'])

    new_review = Review(
        user_id=data['user_id'],
        room_id=data['room_id'],
        rating=data['rating'],
        comment=cleaned_comment
    )

    db.session.add(new_review)
    db.session.commit()

    # Log the audit event
    audit_logger.info(f"Review Submitted: User {data['user_id']} rated Room {data['room_id']} with {data['rating']} stars.")

    return jsonify({'message': 'Review submitted successfully', 'review': new_review.to_dict()}), 201

@app.route('/reviews/room/<int:room_id>', methods=['GET'])
def get_room_reviews(room_id):
    """Retrieve all reviews for a specific meeting room (filtering out flagged ones)."""
    reviews = Review.query.filter_by(room_id=room_id, is_flagged=False).all()
    return jsonify([review.to_dict() for review in reviews]), 200

@app.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """Update an existing review."""
    data = request.get_json()
    review = Review.query.get_or_404(review_id)

    if 'rating' in data:
        if not (1 <= data['rating'] <= 5):
            return jsonify({'message': 'Rating must be between 1 and 5'}), 400
        review.rating = data['rating']

    if 'comment' in data:
        review.comment = bleach.clean(data['comment'])

    db.session.commit()
    audit_logger.info(f"Review updated: review ID {review_id} was updated.")
    return jsonify({'message': 'Review updated successfully'}), 200

@app.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Delete a review."""
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    audit_logger.warning(f"Review deleted: review ID {review_id} was removed.")
    return jsonify({'message': 'Review deleted successfully'}), 200

@app.route('/reviews/moderate/<int:review_id>', methods=['POST'])
def moderate_review(review_id):
    """Flags a review as inappropriate."""
    data = request.get_json()
    review = Review.query.get_or_404(review_id)

    if data.get('action') == 'flag':
        review.is_flagged = True
        db.session.commit()
        audit_logger.warning(f"Review moderated: review ID {review_id} flagged.")
        return jsonify({'message': 'Review has been flagged and hidden'}), 200
   
    return jsonify({'message': 'Invalid moderation action'}), 400

# --- 5. Logs Endpoint (Phase 2) ---
@app.route('/reviews/logs', methods=['GET'])
def get_audit_logs():
    """Retrieve audit logs."""
    try:
        # Assuming audit.log is in the container's root
        with open('audit.log', 'r') as log_file:
            logs = log_file.readlines()
        return jsonify({'logs': logs}), 200
    except FileNotFoundError:
        return jsonify({'message': 'No audit logs found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5004)