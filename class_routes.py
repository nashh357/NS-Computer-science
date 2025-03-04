from flask import Blueprint, request, jsonify
from db import create_class, get_classes, add_quiz_to_class

class_routes = Blueprint('class', __name__)

@class_routes.route('/classes', methods=['GET'])
def get_classes_route():
    classes = get_classes()
    return jsonify(classes)

@class_routes.route('/classes', methods=['POST'])
def create_class_route():
    data = request.json
    class_name = data.get('name')
    created_by = data.get('createdBy')
    class_code = create_class(class_name, created_by)
    return jsonify({"class_code": class_code}), 201

@class_routes.route('/classes/<class_code>/quizzes', methods=['POST'])
def add_quiz_route(class_code):
    quiz_data = request.json
    add_quiz_to_class(class_code, quiz_data)
    return jsonify({"message": "Quiz added successfully!"}), 201
