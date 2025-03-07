import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import logging
import random
import string
import bcrypt

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Firebase
try:
    cred = credentials.Certificate("C:\\Users\\jesus\\project\\NS-Computer-science\\quizproject-a6230-firebase-adminsdk-fbsvc-d50c78bde1.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.info("Firebase initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Firebase: {e}")
    raise

# Import routes
from auth import auth_routes
from class_routes import class_routes

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management

# Register blueprints
app.register_blueprint(auth_routes)
app.register_blueprint(class_routes)

# Helper Functions
def generate_class_code():
    """Generate a unique class code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_hashed_password_from_db(email):
    """Fetch the hashed password from the database based on the user's email."""
    user_ref = db.collection('users').document(email).get()
    if user_ref.exists:
        return user_ref.to_dict().get('password')
    return None

def check_if_teacher():
    """Check if the current user is a teacher."""
    return session.get('user_role') == 'teacher'

def get_classes_for_user(user_id):
    """Fetch classes for the user (either teacher or student)."""
    return db.collection('classes').where('students', 'array_contains', user_id).stream()

@app.route('/join_class/<class_code>', methods=['POST'])
def join_class(class_code):
    """Join a class using the class code."""
    user_id = session.get('user_uid')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        class_ref = db.collection('classes').document(class_code)
        if not class_ref.get().exists:
            return jsonify({"error": "Class not found"}), 404

        # Add the student to the class
        class_ref.update({
            'students': firestore.ArrayUnion([user_id])
        })
        return jsonify({"success": True}), 200
    except Exception as e:
        logging.error(f"Error joining class: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/create_class', methods=['POST'])
def create_class():
    """Create a new class."""
    data = request.get_json()
    class_name = data.get('name')
    class_description = data.get('description')
    created_by = session.get('user_uid')  # Use the logged-in teacher's UID
    class_code = generate_class_code()

    # Add the class to Firestore
    try:
        db.collection('classes').document(class_code).set({
            'name': class_name,
            'description': class_description,
            'created_by': created_by,
            'class_code': class_code,
            'students': []  # Initialize with an empty list of students
        })
        return jsonify({"success": True, "class_code": class_code}), 201
    except Exception as e:
        logging.error(f"Error creating class: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete_class/<class_code>', methods=['DELETE'])
def delete_class(class_code):
    """Delete a class."""
    try:
        db.collection('classes').document(class_code).delete()
        return '', 204
    except Exception as e:
        logging.error(f"Error deleting class: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/student_dashboard')
def student_dashboard():
    """Render the student dashboard."""
    if 'user_uid' not in session:
        return redirect('/login')

    try:
        classes = list(get_classes_for_user(session['user_uid']))
        logging.debug(f"Raw classes data: {[cls.to_dict() for cls in classes]}")
        formatted_classes = [{
            'name': cls.to_dict().get('name'),
            'description': cls.to_dict().get('description'),
            'class_code': cls.id,
            'assignments': []
        } for cls in classes]

        logging.debug(f"Formatted classes data: {formatted_classes}")
        return render_template('student_dashboard.html', classes=formatted_classes)

    except Exception as e:
        logging.error(f"Error fetching student dashboard data: {e}")
        return "An error occurred", 500

@app.route('/teacher_dashboard')
def teacher_dashboard():
    """Render the teacher dashboard."""
    if 'user_uid' not in session:
        return redirect('/login')

    try:
        classes = list(db.collection('classes').where('created_by', '==', session['user_uid']).stream())
        formatted_classes = []
        for cls in classes:
            class_data = cls.to_dict()
            # Fetch assignments for this class
            assignments_ref = db.collection('classes').document(cls.id).collection('assignments').stream()
            assignments = [assignment.to_dict() for assignment in assignments_ref]
            
            formatted_classes.append({
                'name': class_data.get('name'),
                'description': class_data.get('description'),
                'class_code': cls.id,
                'assignments': assignments
            })

        return render_template('teacher_dashboard.html', classes=formatted_classes)
    except Exception as e:
        logging.error(f"Error fetching teacher dashboard data: {e}")
        return "An error occurred", 500

@app.route('/classes/<class_code>/quizzes', methods=['GET', 'POST'])
def quizzes(class_code):
    """Add a quiz assignment to a class."""
    # Allow both teachers and students to access quizzes
    user_id = session.get('user_uid')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    try:
        # Handle adding a quiz
        if not all(key in data for key in ['name', 'due_date']):
            return jsonify({"error": "Missing required fields"}), 400

            
        # Add the quiz/assignment, ensuring no duplicates

        # Verify database connection
        if not db:
            raise Exception("Database connection not established")
            
        # Create assignment data
        assignment_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'due_date': data.get('due_date'),
            'type': data.get('type', 'assignment'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'status': 'active'
        }
        logging.debug(f"Storing assignment data: {assignment_data}")
        
        # Store in Firestore
        # Check for existing quizzes to prevent duplicates
        existing_quizzes = db.collection('classes').document(class_code).collection('quizzes').where('name', '==', assignment_data['name']).get()
        if existing_quizzes:
            return jsonify({"error": "Quiz with this name already exists."}), 400
        
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').add(assignment_data)

        logging.info(f"Assignment stored successfully with ID: {quiz_ref.id}")

        return jsonify({
            "success": True,
            "quiz_id": quiz_ref.id,
            "message": "Assignment added successfully"
        }), 201
    except Exception as e:
        logging.error(f"Error adding quiz: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to add assignment"
        }), 500


@app.route('/classes/<class_code>/assignments', methods=['POST'])
def add_assignment(class_code):
    """Add an assignment to a class."""
    if not check_if_teacher():
        return "Unauthorized", 403

    data = request.json
    try:
        db.collection('classes').document(class_code).collection('assignments').add({
            'name': data.get('name'),
            'description': data.get('description'),
            'due_date': data.get('due_date'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'type': data.get('type')  # 'multiple_choice' or 'open_ended'
        })
        return jsonify({"success": True}), 201
    except Exception as e:
        logging.error(f"Error adding assignment: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/classes/<class_code>/quizzes/<quiz_id>', methods=['GET'])
def get_quiz(class_code, quiz_id):
    """Fetch a specific quiz by ID."""
    try:
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return jsonify({"error": "Quiz not found"}), 404
        
        quiz_data = quiz_ref.to_dict()
        return render_template('quiz.html', quiz=quiz_data)
    except Exception as e:
        logging.error(f"Error fetching quiz: {e}")
        return jsonify({"error": str(e)}), 500

def submit_quiz(quiz_id):
    """Handle quiz submission.""" 
    try:
        answers = request.form.to_dict()
        user_id = session.get('user_uid')
        db.collection('quiz_submissions').add({
            'quiz_id': quiz_id,
            'user_id': user_id,
            'answers': answers,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return redirect(url_for('dashboard'))
    except Exception as e:
        logging.error(f"Error submitting quiz: {e}")
        return "An error occurred", 500

@app.route('/quiz_results/<quiz_id>')
def quiz_results(quiz_id):
    """Render quiz results for teachers.""" 
    if not check_if_teacher():
        return "Unauthorized", 403

    try:
        submissions_ref = db.collection('quiz_submissions').where('quiz_id', '==', quiz_id).stream()
        submissions = [submission.to_dict() for submission in submissions_ref]
        return render_template('quiz_results.html', 
                               submissions=submissions,
                               total_submissions=len(submissions))
    except Exception as e:
        logging.error(f"Error fetching quiz results: {e}")
        return "An error occurred", 500

if __name__ == "__main__":
    app.run(debug=True)
