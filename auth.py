from flask import Blueprint, request, jsonify, render_template, redirect
from db import get_hashed_password_from_db
import firebase_admin

from firebase_admin import auth
from db import save_user_data  # Import the save_user_data function
import bcrypt  # Import bcrypt for password hashing

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
            return render_template('signup.html', error="Missing fields", email_error="Email is required." if not email else "", password_error="Password is required." if not password else "", name_error="Name is required." if not name else "")

        if not is_valid_password(password):
            return render_template('signup.html', error="Password must be at least 8 characters long, contain an uppercase letter and a number.", password_error="Password must be at least 8 characters long, contain an uppercase letter and a number.")

        try:
            # Check if the email already exists
            user = auth.get_user_by_email(email)
            return render_template('signup.html', error="Email already exists.", email_error="Email already exists.")

        except firebase_admin.auth.UserNotFoundError:
            # Email does not exist, proceed to create user
            try:
                # Create user in Firebase with plain text password
                user = auth.create_user(email=email, password=password)

                # Hash the password for your own database
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                save_user_data(user.uid, name, email, hashed_password.decode('utf-8'), 'regular')  # Save hashed password with user type

                return redirect('/?success=Signup successful!'), 302

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
            return render_template('login.html', error="Missing fields", email_error="Email is required." if not email else "", password_error="Password is required." if not password else "")

        try:
            user = auth.get_user_by_email(email)
            # Retrieve the hashed password from the database
            hashed_password = get_hashed_password_from_db(user.uid)  # This function needs to be implemented
            if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                print("Invalid login credentials.")
                return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")

            print("User found, password verification succeeded.")
            return redirect('/login?success=Login successful!'), 302  # Redirect with success message

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return render_template('login.html', error="Invalid login credentials.", email_error="Invalid email or password.")

    return render_template('login.html')

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
