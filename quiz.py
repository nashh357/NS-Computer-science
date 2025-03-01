from flask import Blueprint, request, jsonify
from db import get_quizzes, submit_answers

quiz_routes = Blueprint('quiz', __name__)

@quiz_routes.route('/quizzes', methods=['GET'])
def get_quizzes_route():
    return get_quizzes()

@quiz_routes.route('/submit_answers', methods=['POST'])
def submit_answers_route():
    answers = request.json.get('answers')
    return submit_answers(answers)
