from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import bleach
import os

try:
    from models import db, Review
    from logger import audit_logger
except ImportError:
    from reviews_service.models import db, Review
    from reviews_service.logger import audit_logger


app = Flask(__name__)

# Use 'db' if in Docker, 'localhost' if local
db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/reviews', methods=['POST'])
def submit_review():
    """
    Submit a new review for a meeting room.

    Expected JSON Input:
        - user_id (int): The ID of the reviewer.
        - room_id (int): The ID of the meeting room being reviewed.
        - rating (int): The rating given to the room (1-5).
        - comment (str): the review text (will be sanitized).

    :return: JSON success message.
    :rtype: tuple
    
    """

    data = request.get_json()

    if not (1 <= data['rating'] <=5):
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

    # log the audit event
    audit_logger.info(f"Review Submitted: User {data['user_id']} rated Room {data['room_id']} with {data['rating']} stars.")

    return jsonify({'message': 'Review submitted successfully'}), 201


@app.route('/reviews/room/<int:room_id>',methods=['GET'])
def get_room_reviews(room_id):
    """
    Retrieve all reviews for a specific meeting room.
    
    **Note**: This endpoint filters out reviews where ``is_flagged`` is True, 
    ensuring that only appropriate content is returned to users.

    :param room_id: The ID of the meeting room.
    :type room_id: int
    :return: JSON list of reviews.
    :rtype: tuple   
    """

    reviews = Review.query.filter_by(room_id=room_id, is_flagged=False).all()
    reviews_list = [review.to_dict() for review in reviews]

    return jsonify(reviews_list), 200

@app.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """
    Update an existing review.

    Expected JSON Input:
        - rating (int): The updated rating (1-5).
        - comment (str): The updated comment.

    :param review_id: The ID of the review to update.
    :type review_id: int
    :return: JSON success message.
    :rtype: tuple
    """

    data = request.get_json()
    review = Review.query.get(review_id)

    if not review:
        return jsonify({'message': 'Review not found'}), 404

    if 'rating' in data:
        if not (1 <= data['rating'] <= 5):
            return jsonify({'message': 'Rating must be between 1 and 5'}), 400
        review.rating = data['rating']

    if 'comment' in data:
        review.comment = bleach.clean(data['comment'])

    db.session.commit()

    # log the audit event
    audit_logger.info(f"Review updated: review ID {review_id} was updated.")

    return jsonify({'message': 'Review updated successfully'}), 200


@app.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """
    Delete a review.

    :param review_id: The ID of the review to delete.
    :type review_id: int
    :return: JSON success message.
    :rtype: tuple
    """

    review = Review.query.get(review_id)

    if not review:
        return jsonify({'message': 'Review not found'}), 404

    db.session.delete(review)
    db.session.commit()

    # log the audit event
    audit_logger.warning(f"Review deleted: review ID {review_id} was removed from the system.")

    return jsonify({'message': 'Review deleted successfully'}), 200

@app.route('/reviews/moderate/<int:review_id>', methods=['POST'])
def moderate_review(review_id):
    """
    Flags a review as inappropriate (Moderation Feature).

    Expected JSON Input:
        - action (str): Must be "flag" to hide the review.
        - reason (str): Optional reason for flagging.

    :param review_id: The ID of the review to moderate.
    :type review_id: int
    :return: JSON success message.
    :rtype: tuple
    """
    data = request.get_json()
    review = Review.query.get(review_id)

    if not review:
        return jsonify({'message': 'Review not found'}), 404

    if data.get('action') == 'flag':
        review.is_flagged = True
        db.session.commit()

        # log the audit event
        audit_logger.warning(f"Review moderated: review ID {review_id} was flagged for the reason: {data.get('reason', 'No reason provided')}")
    
        return jsonify({'message': 'Review has been flagged and hidden'}), 200
    
    return jsonify({'message': 'Invalid moderation action'}), 400


# this is for phase 2 logging
@app.route('/reviews/logs', methods=['GET'])
def get_audit_logs():
    """
    Retrieve audit logs related to review activities.

    :return: JSON list of audit log entries.
    :rtype: tuple
    """
    try:
        with open('audit.log', 'r') as log_file:
            logs = log_file.readlines()
        
        return jsonify({'logs': logs}), 200
    except FileNotFoundError:
        return jsonify({'message': 'No audit logs found'}), 404




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5004)