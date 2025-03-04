from flask import Flask, render_template
from auth import auth_routes
from quiz import quiz_routes

from class_routes import class_routes  # Importing class routes


app = Flask(__name__)

app.register_blueprint(class_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(quiz_routes)

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')
if __name__ == "__main__":
    app.run(debug=True)
