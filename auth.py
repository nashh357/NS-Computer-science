from flask import Blueprint, request, render_template, redirect, jsonify
from db import get_hashed_password_from_db, save_user_data, db
import firebase_admin
from firebase_admin import credentials, auth
import bcrypt  # Import bcrypt for password hashing

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate("path/to/your/firebase/credentials.json")
    firebase_admin.initialize_app(cred)

auth_routes = Blueprint('auth', __name__)

def is_valid_password(password):
    # Example password validation: at least 8 characters, 1 uppercase, 1 number
    return len(password) >= 8 and any(char.isupper() for char in password) and any(char.isdigit() for char in password)

@auth_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        # Debugging: Log incoming form data
        print(f"Signup data: email={email}, password={password}, name={name}")

        if not email or not password or not name:
            return render_template('signup.html', error="Missing fields", 
                                   email_error="Email is required." if not email else "", 
                                   password_error="Password is required." if not password else "", 
                                   name_error="Name is required." if not name else "")

        if not is_valid_password(password):
            return render_template('signup.html', error="Password must be at least 8 characters long, contain an uppercase letter and a number.",
                                   password_error="Password must be at least 8 characters long, contain an uppercase letter and a number.")

        try:
            # Check if the email already exists in Firebase Authentication
            user = auth.get_user_by_email(email)
            return render_template('signup.html', error="Email already exists.", email_error="Email already exists.")
        except auth.UserNotFoundError:
            # Email does not exist, proceed to create user
            try:
                # Create user in Firebase with plain text password
                user = auth.create_user(email=email, password=password)
                print(f"User created in Firebase: {user.uid}")  # Log user creation

                # Hash the password for your own database
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                role = 'student'  # Or dynamically assign based on input
                print(f"Attempting to save user data: UID={user.uid}, Name={name}, Email={email}, Role={role}")  # Log the data being passed
                save_user_data(user.uid, name, email, hashed_password.decode('utf-8'), role)  # Save hashed password with user type


                return redirect('/?success=Signup successful!')

            except Exception as e:
                return render_template('signup.html', error=str(e))

    return render_template('signup.html')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Debugging: Log incoming form data
        print(f"Login data: email={email}, password={password}")

        if not email or not password:
            return render_template('login.html', error="Missing fields", 
                                   email_error="Email is required." if not email else "", 
                                   password_error="Password is required." if not password else "")

        try:
            # Attempt to get the user from Firebase Authentication
            print(f"Attempting to find user with email: {email}")
            user = auth.get_user_by_email(email)
            print(f"User found: {user.uid}")  # Debugging: user found

            # Retrieve the hashed password from your database
            hashed_password = get_hashed_password_from_db(email)  # Use email as the document ID

            if not hashed_password:
                print("No hashed password found in the database.")
                return render_template('login.html', error="User does not exist in Firestore.", email_error="Invalid email or password.")

            # Check if the password matches using bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                print("Password match successful.")  # Debugging statement
                # Now retrieve user data from Firestore
                # Try fetching by email first, then by UID as fallback
                user_query = db.collection("users").where("email", "==", email).limit(1)
                user_docs = user_query.stream()
                
                user_data = None
                for doc in user_docs:
                    user_data = doc
                    break
                
                if not user_data:
                    # Fallback to UID-based lookup
                    user_ref = db.collection("users").document(user.uid)
                    print(f"Fetching user data from Firestore for UID: {user.uid}")  # Log the UID being used
                    print(f"Firestore document path: users/{user.uid}")  # Log the full document path
                    user_data = user_ref.get()
                
                print(f"User data fetched: {user_data.to_dict() if user_data and user_data.exists else 'No data found'}")  # Debugging statement

                print(f"User UID: {user.uid}")  # Log the user UID for debugging
                print(f"User email: {email}")  # Log the user email for debugging


                if not user_data.exists:
                    print("User data not found in Firestore.")  # Log if user data is not found
                    return render_template('login.html', error="User data not found.")  # Ensure proper indentation

                role = user_data.to_dict().get("role", "student")  # Default to "student" if no role found
                print(f"Role fetched: {role}")  # Debugging statement
                print(f"User role: {role}")  # Debugging statement

                # Redirect based on role
                if role == "student":
                    print("Redirecting to student dashboard.")
                    return redirect('/student_dashboard')
                elif role == "teacher":
                    print("Redirecting to teacher dashboard.")
                    return redirect('/teacher_dashboard')
                elif role == "admin":
                    print("Redirecting to admin dashboard.")
                    return redirect('/admin_dashboard')
                else:
                    return redirect('/?error=Unknown role')
            else:
                print("Invalid login credentials: Password mismatch.")
                return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")

        except firebase_admin.auth.UserNotFoundError:
            print("Invalid email or password: User not found.")
            return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")
        except Exception as e:
            print(f"Error during login: {str(e)}")  # More detailed error logging
            return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")

    return render_template('login.html')

@auth_routes.route('/profile', methods=['GET'])
def get_profile():
    """Returns the user's profile information"""
    user = auth.get_user(request.args.get('uid'))
    return jsonify({
        'name': user.display_name,
        'email': user.email,
        'created_at': user.user_metadata.creation_timestamp
    })

@auth_routes.route('/forgot_password', methods=['POST'])
def forgot_password():

    email = request.json.get('email')
    if not email:
        return jsonify({"error": "Missing email"}), 400

    try:
        auth.generate_password_reset_link(email)
        return jsonify({"message": "Password reset link sent"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
