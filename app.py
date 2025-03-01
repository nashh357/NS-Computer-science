from flask import Flask, render_template
from auth import auth_routes
from quiz import quiz_routes

app = Flask(__name__)

app.register_blueprint(auth_routes)
app.register_blueprint(quiz_routes)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
