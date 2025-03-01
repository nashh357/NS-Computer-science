import firebase_admin
from firebase_admin import credentials, firestore

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

def save_user_data(user_id, name, email, password, user_type):
    # Save user data to Firestore
    users_ref = db.collection('users')
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
