from flask import Blueprint, request, jsonify, session, render_template
from db import create_class, get_classes, add_quiz_to_class, db

def get_students():
    # Logic to get students
    return []

class_routes = Blueprint('class', __name__)

@class_routes.route('/classes', methods=['GET'])
def get_classes_route():
    teacher_id = session.get('user_uid')  # Get the logged-in teacher's UID
    classes = get_classes(created_by=teacher_id)  # Pass the teacher's UID to filter classes
    return jsonify({"classes": [{**class_doc.to_dict(), "id": class_doc.id} for class_doc in classes], "students": get_students()})  # Ensure the response includes both classes and student data






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

@class_routes.route('/classroom/<class_code>', methods=['GET'])
def classroom_route(class_code):
    # Fetch class data from Firestore
    class_doc = db.collection('classes').document(class_code).get()
    if not class_doc.exists:
        return "Classroom not found", 404
    
    class_data = class_doc.to_dict()
    
    # Fetch quizzes for this class
    quizzes_ref = db.collection('classes').document(class_code).collection('quizzes')
    quizzes = [quiz.to_dict() for quiz in quizzes_ref.stream()]
    
    # Check if user is teacher
    is_teacher = session.get('user_role') == 'teacher'
    
    return render_template('classroom.html', 
                         class_data=class_data, 
                         quizzes=quizzes,
                         is_teacher=is_teacher)

@class_routes.route('/classes/<class_code>/performance', methods=['GET'])

@class_routes.route('/classes/<class_code>', methods=['DELETE'])

def delete_class_route(class_code):
    # Check if the user is a teacher
    user_role = session.get('user_role')  # Assuming user role is stored in session
    if user_role != 'teacher':
        return jsonify({"message": "Unauthorized to delete class."}), 403

    # Logic to delete a class from Firestore
    db.collection('classes').document(class_code).delete()
def get_performance_route(class_code):
    # Logic to retrieve student performance stats for the class using class_code
    performance_data = {}  # Replace with actual logic to get performance data
    # Logic to retrieve student performance stats for the class
    return jsonify({"class_code": class_code, "performance_data": performance_data, "message": "Performance data retrieved successfully!"}), 200

