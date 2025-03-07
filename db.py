import firebase_admin
from firebase_admin import credentials, firestore

# Check if the app is already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("quizproject-a6230-firebase-adminsdk-fbsvc-d50c78bde1.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_quizzes():
    # Fetch quiz questions from Firestore
    quizzes_ref = db.collection('quizzes')
    quizzes = quizzes_ref.stream()
    return {quiz.id: quiz.to_dict() for quiz in quizzes}

def submit_answers(answers):
    # Handle answer submission
    results_ref = db.collection('results')
    results_ref.add(answers)
    return {"message": "Answers submitted successfully!"}

def get_hashed_password_from_db(email):
    # Retrieve the hashed password for the user from Firestore
    users_ref = db.collection('users')
    # Query the users collection by email instead of using the email as the document ID
    user_query = users_ref.where('email', '==', email).limit(1)
    user_doc = user_query.stream()

    for doc in user_doc:
        return doc.to_dict().get('password')  # Return the hashed password
    return None  # Return None if user does not exist

def save_user_data(user_id, name, email, password, user_type):
    # Save user data to Firestore
    users_ref = db.collection('users')
    # Check if user already exists
    user_doc = users_ref.document(user_id).get()
    if user_doc.exists:
        print(f"User with ID {user_id} already exists.")
        return  # Avoid overwriting existing user data

    try:
        users_ref.document(user_id).set({
            'name': name,
            'email': email,
            'password': password,  # Save the password in the correct field
            'user_type': user_type  # Save the user type
        })
        print(f"User data saved: {user_id}, {name}, {email}, {user_type}")

    except Exception as e:
        print(f"Error saving user data: {str(e)}")

def create_class(name, created_by):
    # Adds a new class document to Firestore
    classes_ref = db.collection('classes')
    class_code = generate_class_code()  # Function to generate a unique class code
    classes_ref.add({
        'name': name,
        'createdBy': created_by,
        'code': class_code
    })
    return class_code

def get_classes(created_by):
    # Retrieves classes from Firestore based on the creator
    classes_ref = db.collection('classes').where('createdBy', '==', created_by)
    classes = classes_ref.stream()
    return [{**class_doc.to_dict(), "id": class_doc.id, "code": class_doc.to_dict().get("code")} for class_doc in classes]


def get_students():
    # Retrieves all students from Firestore
    users_ref = db.collection('users').where('user_type', '==', 'student')
    students = users_ref.stream()
    student_list = []
    for student in students:
        student_data = student.to_dict()
        if 'name' in student_data:  # Check if 'name' field exists
            student_list.append({**student_data, "id": student.id})
        else:
            print(f"Student document {student.id} does not have a 'name' field.")
    return student_list


def add_quiz_to_class(class_code, quiz_data):
    # Adds a quiz to a specific class
    quizzes_ref = db.collection('classes').document(class_code).collection('quizzes')
    quizzes_ref.add(quiz_data)

def generate_class_code():
    # Function to generate a unique class code
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
