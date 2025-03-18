import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import logging
import random
import string
import bcrypt
from datetime import datetime
import warnings

# Suppress specific UserWarning about using positional arguments in Firestore queries
warnings.filterwarnings("ignore", message="Detected filter using positional arguments.*")

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Firebase
try:
    cred = credentials.Certificate("quizproject-a6230-firebase-adminsdk-fbsvc-ae201fd420.json")
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

    if request.method == 'GET':
        # Get all quizzes for this class
        try:
            quizzes_ref = db.collection('classes').document(class_code).collection('quizzes').stream()
            quizzes_list = []
            for quiz in quizzes_ref:
                quiz_data = quiz.to_dict()
                quiz_data['id'] = quiz.id
                quizzes_list.append(quiz_data)
            return jsonify(quizzes_list), 200
        except Exception as e:
            logging.error(f"Error fetching quizzes: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Handle adding a quiz (POST)
    try:
        data = request.json
        if not data or not all(key in data for key in ['name', 'due_date']):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Create assignment data
        assignment_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'due_date': data.get('due_date'),
            'type': data.get('type', 'multiple_choice'),
            'created_at': firestore.SERVER_TIMESTAMP,
            'status': 'active',
            'created_by': user_id
        }
        
        # Add questions to the assignment
        if 'questions' in data and isinstance(data['questions'], list):
            assignment_data['questions'] = data['questions']
        
        # Store in Firestore
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').add(assignment_data)
        quiz_id = quiz_ref[1].id

        return jsonify({
            "success": True,
            "quiz_id": quiz_id,
            "message": "Assignment added successfully"
        }), 201
    except Exception as e:
        logging.error(f"Error adding quiz: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to add assignment"
        }), 500


@app.route('/classes/<class_code>/quizzes/<quiz_id>', methods=['GET'])
def get_quiz(class_code, quiz_id):
    """Fetch a specific quiz by ID."""
    try:
        user_id = session.get('user_uid')
        if not user_id:
            return redirect('/login')
            
        # Get the quiz document
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            logging.error(f"Quiz not found: {quiz_id} in class {class_code}")
            return render_template('error.html', error="Quiz not found"), 404
        
        # Extract quiz data
        quiz_data = quiz_ref.to_dict()
        quiz_data['id'] = quiz_id
        logging.debug(f"Retrieved quiz data: {quiz_data}")
        
        # Extract questions directly from the quiz document
        questions = quiz_data.get('questions', [])
        
        # If there are no questions in the quiz document, check for a separate questions collection
        if not questions:
            logging.debug("No questions found in quiz document, checking questions collection")
            questions_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).collection('questions').stream()
            questions = []
            for q in questions_ref:
                question = q.to_dict()
                question['id'] = q.id
                questions.append(question)
                
        logging.debug(f"Final questions list: {questions}")
        
        return render_template('quiz.html', 
                               quiz=quiz_data, 
                               questions=questions, 
                               quiz_id=quiz_id, 
                               class_code=class_code)
    except Exception as e:
        logging.error(f"Error fetching quiz: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/classes/<class_code>/quizzes/<quiz_id>/submit', methods=['POST'])
def submit_quiz(class_code, quiz_id):
    """Handle quiz submission."""
    try:
        user_id = session.get('user_uid')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Get the answers from JSON request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        logging.debug(f"Received quiz submission: {data}")
        
        # Format the submission data
        answers = {}
        for key, value in data.items():
            if key.startswith('question_'):
                question_index = key.split('_')[1]
                answers[question_index] = value
        
        # Ensure we have the quiz ID and class code from the form data if not in URL
        if 'quiz_id' in data and not quiz_id:
            quiz_id = data['quiz_id']
        if 'class_code' in data and not class_code:
            class_code = data['class_code']
            
        logging.debug(f"Processing submission for quiz {quiz_id} in class {class_code}")
        
        # Include metadata
        submission_data = {
            'quiz_id': quiz_id,
            'class_code': class_code,
            'user_id': user_id,
            'answers': answers,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'score': None,  # Will be calculated when grading
            'graded': False
        }
        
        logging.debug(f"Formatted submission data: {submission_data}")
        
        # Get the quiz to check answers
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return jsonify({"error": "Quiz not found"}), 404
            
        quiz_data = quiz_ref.to_dict()
        questions = quiz_data.get('questions', [])
        
        # Auto-grade multiple choice questions
        if questions:
            correct_count = 0
            total_questions = len(questions)
            
            for i, question in enumerate(questions):
                question_idx = str(i)
                # Skip if the question wasn't answered
                if question_idx not in answers:
                    continue
                    
                student_answer = answers[question_idx]
                
                # Only count this as a multiple choice question if it has options
                if 'options' in question:
                    # Fix for quizzes with 'multiple_choice' type or no type specified
                    question_type = question.get('type', 'multiple_choice')
                    
                    # For multiple choice questions, check the answer
                    if question_type == 'multiple_choice' or question_type is None:
                        for option in question.get('options', []):
                            if option.get('isCorrect') and student_answer == option.get('text'):
                                correct_count += 1
            
            # Calculate score as percentage
            if total_questions > 0:
                score_percentage = (correct_count / total_questions) * 100
                submission_data['score'] = score_percentage
                submission_data['graded'] = True
                submission_data['correct_count'] = correct_count
                submission_data['total_questions'] = total_questions
        
        # Save the submission to Firestore
        submission_ref = db.collection('quiz_submissions').add(submission_data)
        submission_id = submission_ref[1].id
        
        # Update the quiz document to mark as submitted for this user
        student_submissions_ref = db.collection('classes').document(class_code).collection('student_submissions')
        student_submissions_ref.document(f"{user_id}_{quiz_id}").set({
            'user_id': user_id,
            'quiz_id': quiz_id,
            'submission_id': submission_id,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'submitted': True
        })
        
        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": "Quiz submitted successfully",
            "redirect": f"/classes/{class_code}/quizzes/{quiz_id}/results"
        }), 200
    except Exception as e:
        logging.error(f"Error submitting quiz: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/classes/<class_code>/quizzes/<quiz_id>/results')
def view_quiz_results(class_code, quiz_id):
    """View results for a specific quiz submission."""
    try:
        user_id = session.get('user_uid')
        if not user_id:
            return redirect('/login')
            
        # Get the quiz
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return render_template('error.html', error="Quiz not found"), 404
            
        quiz_data = quiz_ref.to_dict()
        quiz_data['id'] = quiz_id
        
        # Get the questions
        questions = quiz_data.get('questions', [])
        
        # Find the user's submission
        submissions_ref = db.collection('quiz_submissions')
        query = submissions_ref.where('user_id', '==', user_id).where('quiz_id', '==', quiz_id).limit(1)
        submission_docs = query.stream()
        
        submission = None
        for doc in submission_docs:
            submission = doc.to_dict()
            submission['id'] = doc.id
            break
            
        if not submission:
            return render_template('error.html', error="You haven't submitted this quiz yet"), 404
        
        # Prepare data for display
        question_results = []
        
        # Associate questions with answers
        for i, question in enumerate(questions):
            result = {
                'question': question.get('question', 'No question text'),
                'type': question.get('type', 'unknown'),
                'options': question.get('options', []),
                'student_answer': submission.get('answers', {}).get(str(i), 'Not answered')
            }
            
            # Add correctness info for multiple choice
            if question.get('type') == 'multiple_choice':
                for option in question.get('options', []):
                    if option.get('isCorrect') and result['student_answer'] == option.get('text'):
                        result['correct_answer'] = option.get('text', '')
                        result['is_correct'] = (result['student_answer'] == result['correct_answer'])
                        break
            
            question_results.append(result)
        
        return render_template('quiz_results.html', 
                               quiz=quiz_data, 
                               submission=submission,
                               question_results=question_results,
                               class_code=class_code)
    except Exception as e:
        logging.error(f"Error viewing quiz results: {e}")
        return render_template('error.html', error=f"Error viewing results: {str(e)}"), 500

@app.route('/teacher/quiz_results/<quiz_id>')
def teacher_quiz_results(quiz_id):
    """View all student submissions for a quiz (teacher view)."""
    try:
        user_id = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_id:
            return redirect('/login')
            
        if user_role != 'teacher':
            return render_template('error.html', error="You do not have permission to view this page"), 403
            
        # Fetch quiz information
        quiz_data = None
        class_code = None
        
        # Find the quiz in the teacher's classes
        teacher_classes = db.collection('classes').where('created_by', '==', user_id).stream()
        for teacher_class in teacher_classes:
            class_dict = teacher_class.to_dict()
            class_code_temp = teacher_class.id
            
            quiz_ref = teacher_class.reference.collection('quizzes').document(quiz_id).get()
            if quiz_ref.exists:
                quiz_data = quiz_ref.to_dict()
                quiz_data['id'] = quiz_id
                class_code = class_code_temp
                break
                
        if not quiz_data:
            return render_template('error.html', error="Quiz not found"), 404
            
        # Fetch class details
        class_ref = db.collection('classes').document(class_code).get()
        class_data = class_ref.to_dict() if class_ref.exists else {'name': 'Unknown Class'}
            
        # Get all student submissions for this quiz
        submissions = []
        
        # Get all submissions for this quiz - use just quiz_id to ensure we get all submissions
        # This is better than filtering by both quiz_id and class_code which might miss some
        submissions_refs = db.collection('quiz_submissions').where('quiz_id', '==', quiz_id).stream()
        
        # Process all submissions
        total_score = 0
        passing_count = 0
        score_distribution = [0, 0, 0, 0, 0]  # Buckets: 0-20%, 21-40%, 41-60%, 61-80%, 81-100%
        total_submissions = 0
        
        for submission_ref in submissions_refs:
            submission = submission_ref.to_dict()
            
            # Skip submissions from different classes (after fetching to ensure we get all)
            if submission.get('class_code') != class_code:
                continue
                
            submission['id'] = submission_ref.id
            
            # Get student information
            student_ref = db.collection('users').document(submission.get('user_id', '')).get()
            student_data = student_ref.to_dict() if student_ref.exists else {}
            
            # Set student information for display
            submission['student_name'] = student_data.get('name', 'Unknown Student')
            submission['student_email'] = student_data.get('email', 'No Email')
            submission['user_name'] = student_data.get('name', 'Unknown Student')  # Ensure user_name is set for template
            submission['user_email'] = student_data.get('email', 'No Email')  # Ensure user_email is set for template
            
            # Format timestamp if it exists
            if 'timestamp' in submission and hasattr(submission['timestamp'], '_seconds'):
                submission['formatted_time'] = datetime.fromtimestamp(
                    submission['timestamp']._seconds
                ).strftime('%Y-%m-%d %H:%M:%S')
            else:
                submission['formatted_time'] = 'N/A'
            
            # Calculate statistics
            score = submission.get('score', 0)
            total_score += score
            if score >= 60:  # Assuming 60% is passing
                passing_count += 1
                
            # Add to score distribution
            if score <= 20:
                score_distribution[0] += 1
            elif score <= 40:
                score_distribution[1] += 1
            elif score <= 60:
                score_distribution[2] += 1
            elif score <= 80:
                score_distribution[3] += 1
            else:
                score_distribution[4] += 1
                
            submissions.append(submission)
            total_submissions += 1
            
        # Calculate average score and pass rate
        avg_score = total_score / total_submissions if total_submissions > 0 else 0
        pass_rate = (passing_count / total_submissions * 100) if total_submissions > 0 else 0
        
        # Get total students in class for completion rate calculation
        quiz_data['total_students'] = len(class_data.get('students', []))
            
        return render_template(
            'teacher_quiz_results.html',
            quiz=quiz_data,
            class_code=class_code,
            class_name=class_data.get('name', 'Unknown Class'),
            submissions=submissions,
            total_submissions=total_submissions,
            avg_score=avg_score,
            pass_rate=pass_rate,
            score_distribution=score_distribution
        )
        
    except Exception as e:
        logging.error(f"Error in teacher quiz results: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/get_class/<class_code>')
def get_class(class_code):
    """Get class details and quizzes."""
    try:
        user_id = session.get('user_uid')
        user_role = session.get('user_role') # Get user role
        if not user_id:
            return redirect('/login')
            
        # Get class data
        class_ref = db.collection('classes').document(class_code).get()
        if not class_ref.exists:
            return render_template('error.html', error="Class not found"), 404
            
        class_data = class_ref.to_dict()
        class_data['class_code'] = class_code
        
        # Get quizzes
        quizzes_ref = db.collection('classes').document(class_code).collection('quizzes').stream()
        quizzes = []
        for quiz in quizzes_ref:
            quiz_data = quiz.to_dict()
            quiz_data['id'] = quiz.id
            
            # Check if user has submitted this quiz
            submission_ref = db.collection('classes').document(class_code)\
                            .collection('student_submissions').document(f"{user_id}_{quiz.id}").get()
            quiz_data['submitted'] = submission_ref.exists
            
            quizzes.append(quiz_data)
            
        # Get assignments
        assignments_ref = db.collection('classes').document(class_code).collection('assignments').stream()
        assignments = []
        for assignment in assignments_ref:
            assignment_data = assignment.to_dict()
            assignment_data['id'] = assignment.id
            
            # Check if user has submitted this assignment
            submission_ref = db.collection('classes').document(class_code)\
                            .collection('assignment_submissions').document(f"{user_id}_{assignment.id}").get()
            assignment_data['submitted'] = submission_ref.exists
            
            assignments.append(assignment_data)
        
        # Separate quizzes and regular assignments
        filtered_quizzes = [q for q in quizzes if q.get('type') == 'quiz']
        filtered_assignments = [a for a in quizzes if a.get('type') == 'assignment']
        filtered_assignments.extend(assignments)
        
        return render_template('classroom.html', 
                               class_data=class_data, 
                               quizzes=filtered_quizzes,
                               assignments=filtered_assignments,
                               is_teacher=(user_role == 'teacher'))
    except Exception as e:
        logging.error(f"Error getting class: {e}")
        return render_template('error.html', error=f"Error loading class: {str(e)}"), 500

@app.route('/classroom/<class_code>')
def classroom(class_code):
    """Redirect to the get_class function for classroom view."""
    return get_class(class_code)

@app.route('/quiz_submission/<submission_id>')
def view_submission(submission_id):
    """Get details of a specific quiz submission."""
    try:
        user_id = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Only teachers can view any submission
        # Students can only view their own submissions
        submission_ref = db.collection('quiz_submissions').document(submission_id).get()
        if not submission_ref.exists:
            return jsonify({"error": "Submission not found"}), 404
            
        submission = submission_ref.to_dict()
        
        # Check permissions
        if user_role != 'teacher' and submission.get('user_id') != user_id:
            return jsonify({"error": "You don't have permission to view this submission"}), 403
        
        # Get user info if it's a teacher viewing
        if user_role == 'teacher':
            user_ref = db.collection('users').document(submission.get('user_id', '')).get()
            if user_ref.exists:
                user_data = user_ref.to_dict()
                submission['user_name'] = user_data.get('name', 'Unknown User')
                submission['user_email'] = user_data.get('email', 'No Email')
        
        # Add correctness information if available
        if 'quiz_id' in submission and 'class_code' in submission:
            quiz_ref = db.collection('classes').document(submission['class_code']).collection('quizzes').document(submission['quiz_id']).get()
            if quiz_ref.exists:
                quiz = quiz_ref.to_dict()
                questions = quiz.get('questions', [])
                
                # Create correctness mapping
                correctness = {}
                for i, question in enumerate(questions):
                    question_idx = str(i)
                    if question_idx not in submission.get('answers', {}):
                        continue
                        
                    student_answer = submission['answers'][question_idx]
                    
                    # For multiple choice
                    if question.get('type') == 'multiple_choice' and 'options' in question:
                        # Fix for quizzes with 'multiple_choice' type or no type specified
                        question_type = question.get('type', 'multiple_choice')
                        
                        # For multiple choice questions, check the answer
                        if question_type == 'multiple_choice' or question_type is None:
                            for option in question.get('options', []):
                                if option.get('isCorrect') and student_answer == option.get('text'):
                                    correctness[question_idx] = 'correct'
                                    break
                        if question_idx not in correctness:
                            correctness[question_idx] = 'incorrect'
                
                submission['correctness'] = correctness
        
        return jsonify(submission)
    except Exception as e:
        logging.error(f"Error viewing submission: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/classes/<class_code>/quizzes/<quiz_id>/results')
def teacher_quiz_analytics(class_code, quiz_id):
    """View detailed analytics for a quiz, including per-question breakdown and open-ended grading."""
    try:
        user_id = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_id:
            return redirect('/login')
            
        if user_role != 'teacher':
            return render_template('error.html', error="You do not have permission to view this page"), 403
        
        # Get the quiz details
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return render_template('error.html', error="Quiz not found"), 404
            
        quiz_data = quiz_ref.to_dict()
        quiz_data['id'] = quiz_id
        
        # Get class info
        class_ref = db.collection('classes').document(class_code).get()
        if not class_ref.exists:
            return render_template('error.html', error="Class not found"), 404
            
        class_data = class_ref.to_dict()
        class_data['class_code'] = class_code
        
        # Get all submissions for this quiz
        submissions = []
        
        # Get all submissions for this quiz - use just quiz_id to ensure we get all submissions
        # This is better than filtering by both quiz_id and class_code which might miss some
        submissions_refs = db.collection('quiz_submissions').where('quiz_id', '==', quiz_id).stream()
        
        # Process all submissions
        total_score = 0
        passing_count = 0
        score_distribution = [0, 0, 0, 0, 0]  # Buckets: 0-20%, 21-40%, 41-60%, 61-80%, 81-100%
        total_submissions = 0
        
        for sub in submissions_refs:
            sub_data = sub.to_dict()
            
            # Skip submissions from different classes (after fetching to ensure we get all)
            if sub_data.get('class_code') != class_code:
                continue
                
            sub_data['id'] = sub.id
            
            # Get student information
            student_ref = db.collection('users').document(sub_data.get('user_id', '')).get()
            student_data = student_ref.to_dict() if student_ref.exists else {}
            
            # Set student information for display
            sub_data['student_name'] = student_data.get('name', 'Unknown')
            sub_data['student_email'] = student_data.get('email', 'No Email')
            sub_data['user_name'] = student_data.get('name', 'Unknown')  # Ensure user_name is set for template
            sub_data['user_email'] = student_data.get('email', 'No Email')  # Ensure user_email is set for template
            
            # Format timestamp if it exists
            if 'timestamp' in sub_data and hasattr(sub_data['timestamp'], '_seconds'):
                sub_data['formatted_time'] = datetime.fromtimestamp(
                    sub_data['timestamp']._seconds
                ).strftime('%Y-%m-%d %H:%M:%S')
            else:
                sub_data['formatted_time'] = 'N/A'
            
            # Calculate statistics
            score = sub_data.get('score', 0)
            total_score += score
            if score >= 60:  # Assuming 60% is passing
                passing_count += 1
                
            # Add to score distribution
            if score <= 20:
                score_distribution[0] += 1
            elif score <= 40:
                score_distribution[1] += 1
            elif score <= 60:
                score_distribution[2] += 1
            elif score <= 80:
                score_distribution[3] += 1
            else:
                score_distribution[4] += 1
                
            submissions.append(sub_data)
            total_submissions += 1
            
        # Calculate overall stats
        if len(submissions) > 0:
            avg_score = total_score / len(submissions)
        
        completion_rate = (len(submissions) / len(class_data.get('students', [])) * 100) if len(class_data.get('students', [])) > 0 else 0
        
        return render_template('teacher_quiz_analytics.html',
                              quiz=quiz_data,
                              class_data=class_data,
                              submissions=submissions,
                              score_distribution=score_distribution,
                              completion_rate=completion_rate,
                              avg_score=avg_score)
                              
    except Exception as e:
        logging.error(f"Error viewing teacher quiz analytics: {e}")
        return render_template('error.html', error=f"Error viewing analytics: {str(e)}"), 500

@app.route('/grade_open_ended', methods=['POST'])
def grade_open_ended():
    """Grade an open-ended question submission."""
    try:
        if session.get('user_role') != 'teacher':
            return jsonify({"error": "Unauthorized"}), 403
            
        data = request.get_json()
        submission_id = data.get('submission_id')
        question_idx = data.get('question_idx')
        grade = data.get('grade')
        
        if not submission_id or question_idx is None or grade is None:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Update the grade in the submission
        submission_ref = db.collection('quiz_submissions').document(submission_id)
        submission = submission_ref.get()
        
        if not submission.exists:
            return jsonify({"error": "Submission not found"}), 404
            
        submission_data = submission.to_dict()
        answers = submission_data.get('answers', [])
        
        if question_idx >= len(answers):
            return jsonify({"error": "Question index out of range"}), 400
            
        # Update the grade and mark as graded
        answers[question_idx]['grade'] = grade
        answers[question_idx]['is_graded'] = True
        
        # Recalculate total score
        total_score = 0
        for answer in answers:
            if answer.get('type') == 'multiple_choice' and answer.get('correct', False):
                total_score += 1
            elif answer.get('type') == 'open_ended' and answer.get('is_graded', False):
                total_score += answer.get('grade', 0)
        
        # Update the submission
        submission_ref.update({
            'answers': answers,
            'score': total_score
        })
        
        return jsonify({"success": True, "new_score": total_score}), 200
        
    except Exception as e:
        logging.error(f"Error grading open-ended question: {e}")
        return jsonify({"error": str(e)}), 500

# Quiz deletion endpoint
@app.route('/classes/<class_code>/quizzes/<quiz_id>', methods=['DELETE'])
def delete_quiz(class_code, quiz_id):
    """Delete a quiz from a class."""
    try:
        user_id = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
            
        # Only teachers can delete quizzes
        if user_role != 'teacher':
            return jsonify({"error": "Only teachers can delete quizzes"}), 403
            
        # Get the class to verify it exists
        class_ref = db.collection('classes').document(class_code).get()
        if not class_ref.exists:
            return jsonify({"error": "Class not found"}), 404
            
        # Get the quiz to verify it exists
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).get()
        if not quiz_ref.exists:
            return jsonify({"error": "Quiz not found"}), 404
            
        # Delete the quiz
        db.collection('classes').document(class_code).collection('quizzes').document(quiz_id).delete()
        
        # Delete all quiz submissions for this quiz
        submissions_ref = db.collection('classes').document(class_code).collection('student_submissions').where('quiz_id', '==', quiz_id).stream()
        for submission in submissions_ref:
            submission.reference.delete()
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error deleting quiz: {e}")
        return jsonify({"error": str(e)}), 500

# Assignment deletion endpoint
@app.route('/classes/<class_code>/assignments/<assignment_id>', methods=['DELETE'])
def delete_assignment(class_code, assignment_id):
    """Delete an assignment from a class."""
    try:
        user_id = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
            
        # Only teachers can delete assignments
        if user_role != 'teacher':
            return jsonify({"error": "Only teachers can delete assignments"}), 403
            
        # Get the class to verify it exists
        class_ref = db.collection('classes').document(class_code).get()
        if not class_ref.exists:
            return jsonify({"error": "Class not found"}), 404
            
        # First check in the quizzes collection for assignments of type 'assignment'
        quiz_ref = db.collection('classes').document(class_code).collection('quizzes').document(assignment_id).get()
        if quiz_ref.exists and quiz_ref.to_dict().get('type') == 'assignment':
            # Delete the assignment from quizzes collection
            db.collection('classes').document(class_code).collection('quizzes').document(assignment_id).delete()
            
            # Delete related submissions
            submissions_ref = db.collection('classes').document(class_code).collection('student_submissions').where('quiz_id', '==', assignment_id).stream()
            for submission in submissions_ref:
                submission.reference.delete()
                
            return jsonify({"status": "success"}), 200
        
        # If not found in quizzes, check in assignments collection
        assignment_ref = db.collection('classes').document(class_code).collection('assignments').document(assignment_id).get()
        if not assignment_ref.exists:
            return jsonify({"error": "Assignment not found"}), 404
            
        # Delete the assignment
        db.collection('classes').document(class_code).collection('assignments').document(assignment_id).delete()
        
        # Delete all assignment submissions for this assignment
        submissions_ref = db.collection('classes').document(class_code).collection('assignment_submissions').where('assignment_id', '==', assignment_id).stream()
        for submission in submissions_ref:
            submission.reference.delete()
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error deleting assignment: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
