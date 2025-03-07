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
cred = credentials.Certificate("C:\\Users\\jesus\\project\\NS-Computer-science\\quizproject-a6230-firebase-adminsdk-fbsvc-d50c78bde1.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

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
    # Placeholder logic; implement actual user role checking
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
        classes = get_classes_for_user(session['user_uid'])
        return render_template('student_dashboard.html', classes=classes)
    except Exception as e:
        logging.error(f"Error fetching student dashboard data: {e}")
        return "An error occurred", 500

@app.route('/teacher_dashboard')
def teacher_dashboard():
    """Render the teacher dashboard."""
    if 'user_uid' not in session:
        return redirect('/login')

    try:
        classes = db.collection('classes').where('created_by', '==', session['user_uid']).stream()
        return render_template('teacher_dashboard.html', classes=classes)
    except Exception as e:
        logging.error(f"Error fetching teacher dashboard data: {e}")
        return "An error occurred", 500

@app.route('/dashboard')
def dashboard():
    """Redirect to the appropriate dashboard based on user role."""
    if 'user_uid' not in session:
        return redirect('/login')

    user_role = session.get('user_role')
    if user_role == 'teacher':
        return redirect('/teacher_dashboard')
    else:
        return redirect('/student_dashboard')

@app.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    email = request.form['email']
    password = request.form['password']
    
    try:
        user = auth.get_user_by_email(email)
        hashed_password = get_hashed_password_from_db(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            session['user_uid'] = user.uid
            session['user_role'] = user.role
            return redirect(url_for('dashboard'))
        return "Invalid credentials", 401
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return "An error occurred", 500

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Fetch classes for the logged-in user."""
    user_id = session.get('user_uid')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        # Check user role
        user_role = session.get('user_role')
        if user_role == 'teacher':
            classes = db.collection('classes').where('created_by', '==', user_id).stream()  # Fetch classes created by the teacher
        else:
            classes = get_classes_for_user(user_id)  # Fetch classes for students

        class_list = [{"name": class_item.id} for class_item in classes]
        return jsonify({"classes": class_list})

    except Exception as e:
        logging.error(f"Error fetching classes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Fetch students for the logged-in teacher."""
    user_id = session.get('user_uid')
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        students_ref = db.collection('users').where('role', '==', 'student').stream()
        students = [{'name': student_doc.to_dict()['name']} for student_doc in students_ref]
        return jsonify({"students": students})
    except Exception as e:
        logging.error(f"Error fetching students: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/quiz/<quiz_id>', methods=['GET'])
def view_quiz(quiz_id):
    """Render the quiz page."""
    try:
        quiz_ref = db.collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return "Quiz not found", 404
        return render_template('quiz.html', quiz=quiz_ref.to_dict())
    except Exception as e:
        logging.error(f"Error fetching quiz: {e}")
        return "An error occurred", 500

@app.route('/submit_quiz/<quiz_id>', methods=['POST'])
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
