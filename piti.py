import tkinter as tk
from tkinter import messagebox
import firebase_admin
from firebase_admin import credentials, auth, firestore
from tkinter import messagebox
# Firebase setup
service_account_path = "quizly.json"
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

class QuizApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Quiz Application")
        self.create_login_page()

    def create_login_page(self):
        self.clear_frame()
        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack(pady=20)

        tk.Label(self.login_frame, text="Login", font=("Helvetica", 16)).grid(row=0, column=1, columnspan=2, pady=10)

        tk.Label(self.login_frame, text="Email:").grid(row=1, column=0, sticky="e")
        self.email_entry = tk.Entry(self.login_frame, width=30)
        self.email_entry.grid(row=1, column=1, columnspan=2, pady=5)

        tk.Label(self.login_frame, text="Password:").grid(row=2, column=0, sticky="e")
        self.password_entry = tk.Entry(self.login_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, columnspan=2, pady=5)

        tk.Label(self.login_frame, text="User Type:").grid(row=3, column=0, sticky="e")
        self.user_type_var = tk.StringVar(value="student")
        tk.Radiobutton(self.login_frame, text="Teacher", variable=self.user_type_var, value="teacher").grid(row=3, column=1, sticky="w")
        tk.Radiobutton(self.login_frame, text="Student", variable=self.user_type_var, value="student").grid(row=3, column=2, sticky="w")

        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=4, column=1, pady=10)
        tk.Button(self.login_frame, text="Sign Up", command=self.create_signup_page).grid(row=4, column=2, pady=10)

    def show_teacher_dashboard(self):
        self.clear_frame()
        dashboard_frame = tk.Frame(self.master)
        dashboard_frame.pack(pady=20)

        tk.Label(dashboard_frame, text="Teacher Dashboard", font=("Helvetica", 16)).grid(row=0, column=0, columnspan=3, pady=10)

        buttons = [
            ("Create New Class", self.create_class_page, 1, 0),
            ("View Class 1", self.view_class_1, 1, 1),
            ("View Class 2", self.view_class_2, 1, 2),
            ("Create New Quiz", self.create_quiz_page, 2, 0),
            ("View Quizzes", self.view_quizzes, 2, 1)
        ]

        for text, command, row, col in buttons:
            btn = tk.Button(dashboard_frame, text=text, font=("Helvetica", 14), width=20, height=5, command=command)
            btn.grid(row=row, column=col, padx=10, pady=10)

        back_button = tk.Button(dashboard_frame, text="Back", font=("Helvetica", 14), command=self.create_login_page)
        back_button.grid(row=3, column=0, columnspan=3, pady=10)

    def create_class_page(self):
        self.clear_frame()
        frame = tk.Frame(self.master)
        frame.pack(pady=20)

        tk.Label(frame, text="Create Class", font=("Helvetica", 16)).pack(pady=10)

        self.class_name_entry = tk.Entry(frame, width=40)
        self.class_name_entry.pack(pady=5)
        self.class_name_entry.insert(0, "Class Name")

        self.class_subject_entry = tk.Entry(frame, width=40)
        self.class_subject_entry.pack(pady=5)
        self.class_subject_entry.insert(0, "Class Subject")

        self.add_student_entry = tk.Entry(frame, width=40)
        self.add_student_entry.pack(pady=5)
        self.add_student_entry.insert(0, "Add Student")

        create_class_button = tk.Button(frame, text="Create Class", font=("Helvetica", 14), command=self.create_class)
        create_class_button.pack(pady=10)

        back_button = tk.Button(frame, text="Back", command=self.show_teacher_dashboard)
        back_button.pack(pady=10)

    def create_quiz_page(self):
        self.clear_frame()
        frame = tk.Frame(self.master)
        frame.pack(pady=20)

        tk.Label(frame, text="Create Quiz", font=("Helvetica", 16)).pack(pady=10)

        self.quiz_name_entry = tk.Entry(frame, width=40)
        self.quiz_name_entry.pack(pady=5)
        self.quiz_name_entry.insert(0, "Quiz Name")

        self.question_entry = tk.Entry(frame, width=40)
        self.question_entry.pack(pady=10)
        self.question_entry.insert(0, "Question 1")

        answer_frame = tk.Frame(frame)
        answer_frame.pack(pady=10)

        self.answer_1_entry = tk.Entry(answer_frame, width=20)
        self.answer_1_entry.grid(row=0, column=0, padx=5, pady=5)
        self.answer_1_entry.insert(0, "Answer 1")

        self.answer_2_entry = tk.Entry(answer_frame, width=20)
        self.answer_2_entry.grid(row=0, column=1, padx=5, pady=5)
        self.answer_2_entry.insert(0, "Answer 2")

        self.answer_3_entry = tk.Entry(answer_frame, width=20)
        self.answer_3_entry.grid(row=1, column=0, padx=5, pady=5)
        self.answer_3_entry.insert(0, "Answer 3")

        self.answer_4_entry = tk.Entry(answer_frame, width=20)
        self.answer_4_entry.grid(row=1, column=1, padx=5, pady=5)
        self.answer_4_entry.insert(0, "Answer 4")

        add_question_button = tk.Button(frame, text="Add Question", font=("Helvetica", 14), command=self.add_question)
        add_question_button.pack(pady=10)

        create_quiz_button = tk.Button(frame, text="Create Quiz", font=("Helvetica", 14), command=self.create_quiz)
        create_quiz_button.pack(pady=10)

        back_button = tk.Button(frame, text="Back", command=self.show_teacher_dashboard)
        back_button.pack(pady=10)

    def create_class(self):
        class_name = self.class_name_entry.get()
        class_subject = self.class_subject_entry.get()
        student_name = self.add_student_entry.get()
        messagebox.showinfo("Success", f"Class '{class_name}' created successfully!")

    def add_question(self):
        messagebox.showinfo("Info", "Question added successfully!")

    def create_quiz(self):
        quiz_name = self.quiz_name_entry.get()
        messagebox.showinfo("Success", f"Quiz '{quiz_name}' created successfully!")

    def clear_frame(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        user_type = self.user_type_var.get()

        if not email or not password:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            user = auth.get_user_by_email(email)
            if user_type == "teacher":
                self.show_teacher_dashboard()
            else:
                self.show_student_dashboard()
        except Exception as e:
            messagebox.showerror("Error", "Login failed. Check your credentials.")

def main():
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    ##ddd