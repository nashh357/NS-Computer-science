from flask import Blueprint, request, jsonify, session, render_template
from db import create_class, get_classes, db, get_assignment_statistics

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
    # Initialize the class in Firestore with default values
    db.collection('classes').document(class_code).set({
        'name': class_name,
        'created_by': created_by,
        'students': [],
        'assignments': [],
        'quizzes': []
    })

    return jsonify({"class_code": class_code}), 201

@class_routes.route('/classes/<class_code>/quizzes', methods=['GET'])
def get_quizzes_for_class(class_code):
    quizzes_ref = db.collection('classes').document(class_code).collection('quizzes').stream()
    quizzes = [{"id": quiz.id, **quiz.to_dict()} for quiz in quizzes_ref]
    if not quizzes:
        return jsonify({"message": "No quizzes found for this class."}), 404
    
    # Pass only the first quiz to the template
    return render_template('quiz.html', quiz=quizzes[0]), 200  # Pass the first quiz in the list

def add_quiz_route(class_code):
    quiz_data = request.json
    # Check for existing quizzes to prevent duplicates
    existing_quizzes = db.collection('classes').document(class_code).collection('quizzes').where('name', '==', quiz_data['name']).get()
    if existing_quizzes:
        return jsonify({"error": "Quiz with this name already exists."}), 400

    # Logic to add quiz to the class in Firestore
    db.collection('classes').document(class_code).collection('quizzes').add(quiz_data)

    return jsonify({"message": "Quiz added successfully!"}), 201

@class_routes.route('/classroom/<class_code>', methods=['GET'])
def classroom_route(class_code):
    # Fetch class data from Firestore
    class_doc = db.collection('classes').document(class_code).get()
    if not class_doc.exists:
        return "Classroom not found", 404
    
    class_data = class_doc.to_dict()
    
    # Fetch assignments for this class
    assignments_ref = db.collection('classes').document(class_code).collection('assignments').stream()
    assignments = [{"id": assignment.id, **assignment.to_dict()} for assignment in assignments_ref]

    # Debugging: Log the assignments data
    print(f"Assignments for class {class_code}: {assignments}")

    # Fetch quizzes for this class
    quizzes_ref = db.collection('classes').document(class_code).collection('quizzes').stream()
    quizzes = [{"id": quiz.id, **quiz.to_dict()} for quiz in quizzes_ref]
    
    # Check if user is teacher
    is_teacher = session.get('user_role') == 'teacher'
    
    return render_template('classroom.html', 
                           class_data=class_data, 
                           quizzes=quizzes,
                           is_teacher=is_teacher,
                           assignments=assignments)

@class_routes.route('/classes/<class_code>/performance', methods=['GET'])
def get_performance_route(class_code):
    # Logic to retrieve student performance stats for the class using class_code
    submissions_ref = db.collection('quiz_submissions').where('class_code', '==', class_code).stream()
    performance_data = [{"user_id": submission.to_dict()['user_id'], "answers": submission.to_dict()['answers']} for submission in submissions_ref]
    return jsonify(performance_data), 200  # Added missing return statement

@class_routes.route('/classes/<class_code>/assignments/<assignment_id>', methods=['DELETE'])
def delete_assignment_route(class_code, assignment_id):
    """Delete an assignment from a specific class."""
    try:
        db.collection('classes').document(class_code).collection('assignments').document(assignment_id).delete()
        return jsonify({"message": "Assignment deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@class_routes.route('/assignment_statistics/<assignment_id>', methods=['GET'])
def assignment_statistics(assignment_id):
    """Fetch statistics for a specific assignment."""
    try:
        statistics = get_assignment_statistics(assignment_id)  # Implement this function in your database module
        return jsonify(statistics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@class_routes.route('/classes/<class_code>', methods=['DELETE'])
def delete_class_route(class_code):
    """Delete a class and its associated quizzes and assignments."""
    # Check if the user is a teacher
    user_role = session.get('user_role')  # Assuming user role is stored in session
    if user_role != 'teacher':
        return jsonify({"message": "Unauthorized to delete class."}), 403

    try:
        # Logic to delete a class and its associated quizzes and assignments from Firestore
        class_ref = db.collection('classes').document(class_code)
        # Delete associated quizzes
        quizzes_ref = class_ref.collection('quizzes').stream()
        for quiz in quizzes_ref:
            quiz.reference.delete()
        # Delete associated assignments
        assignments_ref = class_ref.collection('assignments').stream()
        for assignment in assignments_ref:
            assignment.reference.delete()
        # Finally, delete the class
        class_ref.delete()
        return jsonify({"message": "Class and associated data deleted successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@class_routes.route('/classes/<class_code>/assignments', methods=['POST'])
def add_assignment_route(class_code):
    assignment_data = request.json
    # Check for existing assignments to prevent duplicates
    existing_assignments = db.collection('classes').document(class_code).collection('assignments').where('name', '==', assignment_data['name']).get()
    if existing_assignments:
        return jsonify({"error": "Assignment with this name already exists."}), 400

    # Logic to add assignment to the class in Firestore
    db.collection('classes').document(class_code).collection('assignments').add(assignment_data)

    return jsonify({"message": "Assignment added successfully!"}), 201
