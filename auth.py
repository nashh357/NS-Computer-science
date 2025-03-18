from flask import Blueprint, request, render_template, redirect, jsonify, session
from db import get_hashed_password_from_db, save_user_data, db
import firebase_admin
from firebase_admin import credentials, auth
import bcrypt

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate("quizproject-a6230-firebase-adminsdk-fbsvc-ae201fd420.json")
    firebase_admin.initialize_app(cred)

auth_routes = Blueprint('auth', __name__)

def is_valid_password(password):
    """Validate password: at least 8 characters, 1 uppercase, 1 number."""
    return len(password) >= 8 and any(char.isupper() for char in password) and any(char.isdigit() for char in password)

@auth_routes.route('/logout', methods=['POST'])
def logout():
    """Clear session and redirect to login page."""
    session.clear()
    return redirect('/login')

@auth_routes.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup."""
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
                role = 'student'  # Default role
                print(f"Attempting to save user data: UID={user.uid}, Name={name}, Email={email}, Role={role}")
                save_user_data(user.uid, name, email, hashed_password.decode('utf-8'), role)

                return redirect('/?success=Signup successful!')

            except Exception as e:
                return render_template('signup.html', error=str(e))

    return render_template('signup.html')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
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
            hashed_password = get_hashed_password_from_db(email)

            if not hashed_password:
                print("No hashed password found in the database.")
                return render_template('login.html', error="User does not exist in Firestore.", email_error="Invalid email or password.")

            # Check if the password matches using bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                print("Password match successful.")
                session['user_uid'] = user.uid  # Save the user's UID to the session



                # Retrieve user data from Firestore
                user_query = db.collection("users").where("email", "==", email).limit(1)
                user_docs = user_query.stream()

                user_data = None
                for doc in user_docs:
                    user_data = doc
                    break

                if not user_data:
                    # Fallback to UID-based lookup
                    user_ref = db.collection("users").document(user.uid)
                    print(f"Fetching user data from Firestore for UID: {user.uid}")
                    user_data = user_ref.get()

                if not user_data.exists:
                    print("User data not found in Firestore.")
                    return render_template('login.html', error="User data not found.")

                role = user_data.to_dict().get("role", "student")  # Default to "student" if no role found
                print(f"Role fetched: {role}")
                
                # Store user role in session
                session['user_role'] = role
                print(f"User role {role} stored in session")

                # Redirect to the appropriate dashboard based on user role
                if role == 'teacher':
                    return redirect('/teacher_dashboard')
                else:
                    return redirect('/student_dashboard')


            else:
                print("Invalid login credentials: Password mismatch.")
                return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")

        except auth.UserNotFoundError:
            print("Invalid email or password: User not found.")
            return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")

    return render_template('login.html')

@auth_routes.route('/profile', methods=['GET'])
def get_profile():
    """Returns the user's profile information."""
    user = auth.get_user(request.args.get('uid'))
    return jsonify({ 


        'name': user.display_name,
        'email': user.email,
        'created_at': user.user_metadata.creation_timestamp
    })

@auth_routes.route('/forgot_password', methods=['POST'])
def forgot_password():
    """Handle password reset request."""
    email = request.json.get('email')
    if not email:
        return jsonify({"error": "Missing email"}), 400

    try:
        auth.generate_password_reset_link(email)
        return jsonify({"message": "Password reset link sent"}), 200 


    except Exception as e:
        return jsonify({"error": str(e)}), 400
