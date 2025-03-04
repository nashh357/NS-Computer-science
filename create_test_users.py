import firebase_admin
from firebase_admin import auth, credentials, firestore
import bcrypt

# Initialize Firebase Admin SDK
cred = credentials.Certificate("quizproject-a6230-firebase-adminsdk-fbsvc-d50c78bde1.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

def hash_password(password):
    # Hash the password with bcrypt and return it as a string
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Function to create a user in Firebase Auth and Firestore
def create_test_user(email, password, full_name, role):
    try:
        # Create user in Firebase Authentication
        user = auth.create_user(
            email=email,
            password=password,
            display_name=full_name
        )

        # Store additional user data in Firestore
        user_data = {
            "email": email,
            "full_name": full_name,
            "role": role,
            "password": hash_password(password)  # Hashing for Firestore storage
        }
        db.collection("users").document(email).set(user_data)
        
        print(f"✅ Test user {email} created successfully! Hashed password stored: {user_data['password']}")


    except Exception as e:
        print(f"❌ Error creating user {email}: {e}")

# Create teacher and student users
create_test_user("teacher1@example.com", "teacherpass123", "Teacher One", "teacher")
create_test_user("student1@example.com", "studentpass123", "Student One", "student")
