import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Initialize Firebase
cred = credentials.Certificate("quizly.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class QuizApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Quiz Application")
        self.user_type = None
        self.current_user = None
        self.create_login_page()

    def create_login_page(self):
        self.clear_frame()
        login_frame = ttk.Frame(self.master, padding=20)
        login_frame.pack(pady=20)

        container = ttk.LabelFrame(login_frame, text="Login", padding=20)
        container.pack()

        ttk.Label(container, text="Email:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.email_entry = ttk.Entry(container, width=30)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(container, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.password_entry = ttk.Entry(container, show="*", width=30)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(container, text="Forgot Password?", command=self.forgot_password).grid(row=2, column=1, pady=10)
        ttk.Button(container, text="Login", command=self.login).grid(row=3, column=1, pady=10)
        ttk.Button(container, text="Sign Up", command=self.create_signup_page).grid(row=4, column=1, pady=10)

    def create_signup_page(self):
        self.clear_frame()
        signup_frame = ttk.Frame(self.master, padding=20)
        signup_frame.pack(pady=20)

        container = ttk.LabelFrame(signup_frame, text="Sign Up", padding=20)
        container.pack()

        ttk.Label(container, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.signup_name_entry = ttk.Entry(container, width=30)
        self.signup_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(container, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.signup_email_entry = ttk.Entry(container, width=30)
        self.signup_email_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(container, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.signup_password_entry = ttk.Entry(container, show="*", width=30)
        self.signup_password_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(container, text="Confirm Password:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.confirm_password_entry = ttk.Entry(container, show="*", width=30)
        self.confirm_password_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(container, text="User Type:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.signup_user_type_var = tk.StringVar(value="student")
        ttk.Radiobutton(container, text="Teacher", variable=self.signup_user_type_var, value="teacher").grid(row=4, column=1, sticky="w")
        ttk.Radiobutton(container, text="Student", variable=self.signup_user_type_var, value="student").grid(row=4, column=1, sticky="e")

        ttk.Button(container, text="Create Account", command=self.signup).grid(row=5, column=1, pady=10)
        ttk.Button(container, text="Back to Login", command=self.create_login_page).grid(row=6, column=1, pady=10)

    def save_user_data(self, user_id, name, email, user_type):
        user_data = {
            "name": name,
            "email": email,
            "user_type": user_type
        }
        db.collection("users").document(user_id).set(user_data)

    def signup(self):
        name = self.signup_name_entry.get()
        email = self.signup_email_entry.get()
        password = self.signup_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        user_type = self.signup_user_type_var.get()

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        try:
            user = auth.create_user(email=email, password=password)
            self.save_user_data(user.uid, name, email, user_type)
            messagebox.showinfo("Success", f"Account created for {user_type}")
            self.create_login_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create account: {e}")

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        try:
            user = auth.get_user_by_email(email)
            self.current_user = user
            user_data = db.collection("users").document(user.uid).get().to_dict()
            self.user_type = user_data.get("user_type", "student")
            
            messagebox.showinfo("Success", f"Logged in as {self.user_type}")
            if self.user_type == "teacher":
                self.show_teacher_dashboard()
            else:
                self.show_student_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to login: {e}")

    def forgot_password(self):
        email = simpledialog.askstring("Forgot Password", "Enter your email:")
        if email:
            try:
                auth.generate_password_reset_link(email)
                messagebox.showinfo("Success", "Password reset email sent!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send reset email: {e}")

    def show_student_dashboard(self):
        self.clear_frame()
        dashboard_frame = ttk.Frame(self.master, padding=20)
        dashboard_frame.pack()

        # Top Row
        ttk.Button(dashboard_frame, text="View Assignments\n📚", command=self.view_assignments, width=20).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(dashboard_frame, text="View Scores\n📊", command=self.view_scores, width=20).grid(row=0, column=1, padx=10, pady=10)

        # Bottom Row
        ttk.Button(dashboard_frame, text="View Leaderboard\n🏆", command=self.view_leaderboard, width=20).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(dashboard_frame, text="Explore Quizzes\n🔍", command=self.explore_quizzes, width=20).grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(dashboard_frame, text="Logout", command=self.create_login_page).grid(row=2, column=0, columnspan=2, pady=20)

    def show_teacher_dashboard(self):
        self.clear_frame()
        dashboard_frame = ttk.Frame(self.master, padding=20)
        dashboard_frame.pack()

        # Top Row
        ttk.Button(dashboard_frame, text="Create New Class\n➕", command=self.create_class, width=20).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(dashboard_frame, text="View Class 1\n🏫", command=lambda: self.view_class(1), width=20).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(dashboard_frame, text="View Class 2\n🏫", command=lambda: self.view_class(2), width=20).grid(row=0, column=2, padx=10, pady=10)

        # Bottom Row
        ttk.Button(dashboard_frame, text="Create New Quiz\n📝", command=self.create_quiz, width=20).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(dashboard_frame, text="View Quizzes\n📋", command=self.view_quizzes, width=20).grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(dashboard_frame, text="Logout", command=self.create_login_page).grid(row=2, column=0, columnspan=3, pady=20)

    # Student Page Functions
    def view_assignments(self):
        self.clear_frame()
        assignments_frame = ttk.Frame(self.master, padding=20)
        assignments_frame.pack()

        ttk.Label(assignments_frame, text="Assignments", font=("Helvetica", 16)).pack(pady=20)

        # Example assignments
        assignments = [
            {"name": "Math Assignment", "due_date": "2025-03-01"},
            {"name": "Science Assignment", "due_date": "2025-03-05"}
        ]

        for assignment in assignments:
            assignment_frame = ttk.Frame(assignments_frame)
            assignment_frame.pack(fill="x", pady=5)

            ttk.Label(assignment_frame, text=assignment["name"]).pack(side="left")
            ttk.Label(assignment_frame, text=f"Due Date: {assignment['due_date']}").pack(side="right")

            ttk.Button(assignment_frame, text="View", command=lambda a=assignment: self.view_assignment_details(a)).pack(side="right", padx=5)

        ttk.Button(assignments_frame, text="Back", command=self.show_student_dashboard).pack(pady=20)

    def view_assignment_details(self, assignment):
        self.clear_frame()
        details_frame = ttk.Frame(self.master, padding=20)
        details_frame.pack()

        ttk.Label(details_frame, text=assignment["name"], font=("Helvetica", 16)).pack(pady=20)
        ttk.Label(details_frame, text=f"Due Date: {assignment['due_date']}").pack(pady=10)

        # Example questions
        questions = [
            {"question": "What is 2 + 2?", "answer": ""},
            {"question": "What is the capital of France?", "answer": ""}
        ]

        for i, q in enumerate(questions):
            ttk.Label(details_frame, text=f"Q{i+1}: {q['question']}").pack()
            entry = ttk.Entry(details_frame, width=50)
            entry.pack(pady=5)
            q["entry"] = entry

        ttk.Button(details_frame, text="Submit", command=lambda: self.submit_assignment(questions)).pack(pady=10)
        ttk.Button(details_frame, text="Back", command=self.view_assignments).pack(pady=20)

    def submit_assignment(self, questions):
        for q in questions:
            q["answer"] = q["entry"].get()
        messagebox.showinfo("Success", "Assignment submitted!")
        self.view_assignments()

    def view_scores(self):
        self.clear_frame()
        scores_frame = ttk.Frame(self.master, padding=20)
        scores_frame.pack()

        ttk.Label(scores_frame, text="Scores", font=("Helvetica", 16)).pack(pady=20)

        # Example scores
        scores = [
            {"name": "Math Assignment", "score": "85/100"},
            {"name": "Science Assignment", "score": "90/100"}
        ]

        for score in scores:
            score_frame = ttk.Frame(scores_frame)
            score_frame.pack(fill="x", pady=5)

            ttk.Label(score_frame, text=score["name"]).pack(side="left")
            ttk.Label(score_frame, text=f"Score: {score['score']}").pack(side="right")

        ttk.Button(scores_frame, text="Back", command=self.show_student_dashboard).pack(pady=20)

    def view_leaderboard(self):
        self.clear_frame()
        leaderboard_frame = ttk.Frame(self.master, padding=20)
        leaderboard_frame.pack()

        ttk.Label(leaderboard_frame, text="Leaderboard", font=("Helvetica", 16)).pack(pady=20)

        # Example leaderboard
        leaderboard = [
            {"name": "Alice", "score": "95/100"},
            {"name": "Bob", "score": "90/100"},
            {"name": "Charlie", "score": "85/100"},
            {"name": "Dave", "score": "80/100"},
            {"name": "Eve", "score": "75/100"}
        ]

        for i, entry in enumerate(leaderboard):
            ttk.Label(leaderboard_frame, text=f"{i+1}. {entry['name']} - {entry['score']}").pack()

        ttk.Button(leaderboard_frame, text="Back", command=self.show_student_dashboard).pack(pady=20)

    def explore_quizzes(self):
        self.clear_frame()
        quizzes_frame = ttk.Frame(self.master, padding=20)
        quizzes_frame.pack()

        ttk.Label(quizzes_frame, text="Explore Quizzes", font=("Helvetica", 16)).pack(pady=20)

        # Math Quizzes
        ttk.Label(quizzes_frame, text="Math", font=("Helvetica", 14)).pack(pady=10)
        math_quizzes = ["Algebra Quiz", "Geometry Quiz", "Calculus Quiz"]
        for quiz in math_quizzes:
            ttk.Button(quizzes_frame, text=quiz, width=20).pack(pady=5)

        # Science Quizzes
        ttk.Label(quizzes_frame, text="Science", font=("Helvetica", 14)).pack(pady=10)
        science_quizzes = ["Biology Quiz", "Chemistry Quiz", "Physics Quiz"]
        for quiz in science_quizzes:
            ttk.Button(quizzes_frame, text=quiz, width=20).pack(pady=5)

        ttk.Button(quizzes_frame, text="Back", command=self.show_student_dashboard).pack(pady=20)

    # Teacher Page Functions
    def create_class(self):
        self.clear_frame()
        create_class_frame = ttk.Frame(self.master, padding=20)
        create_class_frame.pack()

        ttk.Label(create_class_frame, text="Create New Class", font=("Helvetica", 16)).pack(pady=20)

        # Class Name
        ttk.Label(create_class_frame, text="Class Name:").pack()
        self.class_name_entry = ttk.Entry(create_class_frame, width=50)
        self.class_name_entry.pack(pady=5)

        # Class Subject
        ttk.Label(create_class_frame, text="Class Subject:").pack()
        self.class_subject_entry = ttk.Entry(create_class_frame, width=50)
        self.class_subject_entry.pack(pady=5)

        # Period
        ttk.Label(create_class_frame, text="Period:").pack()
        self.period_entry = ttk.Entry(create_class_frame, width=50)
        self.period_entry.pack(pady=5)

        ttk.Button(create_class_frame, text="Create Class", command=self.save_class).pack(pady=10)
        ttk.Button(create_class_frame, text="Back", command=self.show_teacher_dashboard).pack(pady=20)

    def save_class(self):
        class_name = self.class_name_entry.get()
        class_subject = self.class_subject_entry.get()
        period = self.period_entry.get()

        if class_name and class_subject and period:
            class_data = {
                "name": class_name,
                "subject": class_subject,
                "period": period
            }
            db.collection("classes").add(class_data)
            messagebox.showinfo("Success", "Class created successfully!")
            self.show_teacher_dashboard()
        else:
            messagebox.showerror("Error", "Please fill in all fields!")

    def view_class(self, class_num):
        self.show_subpage(f"View Class {class_num}")

    def create_quiz(self):
        self.show_subpage("Create New Quiz")

    def view_quizzes(self):
        self.show_subpage("View Quizzes")

    def show_subpage(self, title):
        self.clear_frame()
        subpage_frame = ttk.Frame(self.master, padding=20)
        subpage_frame.pack()

        ttk.Label(subpage_frame, text=title, font=("Helvetica", 16)).pack(pady=20)
        ttk.Button(subpage_frame, text="Back", command=self.show_previous_dashboard).pack()

    def show_previous_dashboard(self):
        if self.user_type == "teacher":
            self.show_teacher_dashboard()
        else:
            self.show_student_dashboard()

    def clear_frame(self):
        for widget in self.master.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()


