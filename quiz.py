from flask import Blueprint, request, jsonify
from db import get_quizzes, submit_answers, db  # Import db for Firestore operations

quiz_routes = Blueprint('quiz', __name__)

@quiz_routes.route('/quizzes', methods=['GET'])
def get_quizzes_route():
    return get_quizzes()

@quiz_routes.route('/quizzes/<quiz_id>/remove_question/<question_id>', methods=['DELETE'])

def remove_question_route(quiz_id, question_id):
    """Remove a question from a specific quiz."""
    try:
        # Logic to remove the question from the Firestore database
        db.collection('quizzes').document(quiz_id).collection('questions').document(question_id).delete()
        return jsonify({"message": "Question removed successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@quiz_routes.route('/attempt_quiz/<quiz_id>', methods=['GET'])
def attempt_quiz_route(quiz_id):
    """Start a quiz attempt."""
    try:
        # Logic to fetch quiz details from Firestore
        quiz_ref = db.collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return jsonify({"error": "Quiz not found"}), 404
        
        quiz_data = quiz_ref.to_dict()
        return jsonify(quiz_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def submit_answers_route():
    answers = request.json.get('answers')
    return submit_answers(answers)
