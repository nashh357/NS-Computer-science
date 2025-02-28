import tkinter as tk
from tkinter import messagebox, simpledialog
import firebase_admin
from firebase_admin import credentials, auth, firestore
import requests


# Path to the service account key file
service_account_path = "quizly.json"


# Initialize Firebase
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)
db = firestore.client()


class QuizApp:
   def __init__(self, master):
       self.master = master
       self.master.title("Quiz Application")
       self.user_type = None
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
      
       tk.Button(self.login_frame, text="Login", command=self.login).grid(row=3, column=1, pady=10)
       tk.Button(self.login_frame, text="Sign Up", command=self.create_signup_page).grid(row=3, column=2, pady=10)
  
   def create_signup_page(self):
       self.clear_frame()
       self.signup_frame = tk.Frame(self.master)
       self.signup_frame.pack(pady=20)
      
       tk.Label(self.signup_frame, text="Sign Up", font=("Helvetica", 16)).grid(row=0, column=1, columnspan=2, pady=10)
      
       tk.Label(self.signup_frame, text="Email:").grid(row=1, column=0, sticky="e")
       self.signup_email_entry = tk.Entry(self.signup_frame, width=30)
       self.signup_email_entry.grid(row=1, column=1, columnspan=2, pady=5)
      
       tk.Label(self.signup_frame, text="Password:").grid(row=2, column=0, sticky="e")
       self.signup_password_entry = tk.Entry(self.signup_frame, show="*", width=30)
       self.signup_password_entry.grid(row=2, column=1, columnspan=2, pady=5)
      
       tk.Label(self.signup_frame, text="User Type:").grid(row=3, column=0, sticky="e")
       self.signup_user_type_var = tk.StringVar(value="student")
       tk.Radiobutton(self.signup_frame, text="Teacher", variable=self.signup_user_type_var, value="teacher").grid(row=3, column=1, sticky="w")
       tk.Radiobutton(self.signup_frame, text="Student", variable=self.signup_user_type_var, value="student").grid(row=3, column=2, sticky="w")
      
       tk.Button(self.signup_frame, text="Sign Up", command=self.signup).grid(row=4, column=1, pady=10)
       tk.Button(self.signup_frame, text="Back to Login", command=self.create_login_page).grid(row=4, column=2, pady=10)
  
   def save_user_data(self, user_id, email, user_type):
       user_data = {
           "email": email,
           "user_type": user_type
       }
       try:
           db.collection("users").document(user_id).set(user_data)
           print(f"User data saved for user_id: {user_id}")
       except Exception as e:
           print(f"Failed to save user data: {e}")
  
   def signup(self):
       email = self.signup_email_entry.get()
       password = self.signup_password_entry.get()
       user_type = self.signup_user_type_var.get()
       try:
           # Check if the email is already registered
           url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
           api_key = "AIzaSyCv8a7tcp16ZnU6ONj3slwhQ7Qw3y8GWig"  # Replace with your Firebase API key
           payload = {
               "email": email,
               "password": password,
               "returnSecureToken": True
           }
           response = requests.post(url, params={"key": api_key}, json=payload)
           response_data = response.json()
          
           if response.status_code == 200:
               user_id = response_data["localId"]
               self.save_user_data(user_id, email, user_type)
               messagebox.showinfo("Success", f"Account created for {user_type}")
               self.create_login_page()
           else:
               error_message = response_data.get("error", {}).get("message", "Unknown error")
               if error_message == "EMAIL_EXISTS":
                   messagebox.showerror("Error", "Email already exists. Please log in.")
               else:
                   raise Exception(error_message)
       except Exception as e:
           messagebox.showerror("Error", f"Failed to create account. Please try again.\n{e}")
           print(f"Failed to create account: {e}")


   def login(self):
       email = self.email_entry.get()
       password = self.password_entry.get()
       try:
           # Firebase Authentication REST API endpoint
           url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
           api_key = "AIzaSyCv8a7tcp16ZnU6ONj3slwhQ7Qw3y8GWig"  # Replace with your Firebase API key
           payload = {
               "email": email,
               "password": password,
               "returnSecureToken": True
           }
           response = requests.post(url, params={"key": api_key}, json=payload)
           response_data = response.json()
          
           if response.status_code == 200:
               user_id = response_data["localId"]
               # Fetch user role from Firestore
               user_doc = db.collection("users").document(user_id).get()
               if user_doc.exists:
                   user_data = user_doc.to_dict()
                   self.user_type = user_data["user_type"]
                   messagebox.showinfo("Success", f"Logged in as {self.user_type}")
                   if self.user_type == "teacher":
                       self.show_teacher_dashboard(response_data)
                   else:
                       self.show_student_dashboard(response_data)
               else:
                   raise Exception("User data not found in Firestore.")
           else:
               raise Exception(response_data.get("error", {}).get("message", "Unknown error"))
       except Exception as e:
           messagebox.showerror("Error", f"Failed to login. Check your credentials.\n{e}")
           print(f"Failed to login: {e}")
      
   def clear_frame(self):
       for widget in self.master.winfo_children():
           widget.destroy()
  
   # -------------------- Teacher Dashboard & Functions --------------------
   def show_teacher_dashboard(self, user):
       self.clear_frame()
       self.teacher_frame = tk.Frame(self.master)
       self.teacher_frame.pack(pady=20)
      
       tk.Label(self.teacher_frame, text="Teacher Dashboard", font=("Helvetica", 16)).pack(pady=10)
       tk.Button(self.teacher_frame, text="Assign Course", command=self.assign_course, width=20).pack(pady=5)
       tk.Button(self.teacher_frame, text="Assign Quiz", command=self.assign_quiz, width=20).pack(pady=5)
       tk.Button(self.teacher_frame, text="Logout", command=self.create_login_page, width=20).pack(pady=5)
      
   def assign_course(self):
       course_name = simpledialog.askstring("Assign Course", "Enter course name:")
       if course_name:
           teacher_id = auth.current_user['localId']
           db.collection("teacher_courses").document(teacher_id).set({"course_name": course_name})
           messagebox.showinfo("Success", f"Course '{course_name}' assigned.")
          
   def assign_quiz(self):
       course_id = simpledialog.askstring("Assign Quiz", "Enter course ID:")
       quiz_title = simpledialog.askstring("Assign Quiz", "Enter quiz title:")
       questions = []
       num_questions = simpledialog.askinteger("Assign Quiz", "How many questions?")
       for i in range(num_questions):
           question = simpledialog.askstring("Question", f"Enter question {i+1}:")
           answer = simpledialog.askstring("Answer", f"Enter answer for question {i+1}:")
           questions.append({"question": question, "answer": answer})
       if course_id and quiz_title and questions:
           quiz_data = {"quiz_title": quiz_title, "questions": questions}
           db.collection("quizzes").document(course_id).set(quiz_data)
           messagebox.showinfo("Success", "Quiz assigned successfully.")
  
   # -------------------- Student Dashboard & Quiz Functions --------------------
   def show_student_dashboard(self, user):
       self.clear_frame()
       self.student_frame = tk.Frame(self.master)
       self.student_frame.pack(pady=20)
      
       tk.Label(self.student_frame, text="Student Dashboard", font=("Helvetica", 16)).pack(pady=10)
       tk.Button(self.student_frame, text="Take Quiz", command=self.take_quiz, width=20).pack(pady=5)
       tk.Button(self.student_frame, text="Logout", command=self.create_login_page, width=20).pack(pady=5)
      
   def take_quiz(self):
       course_id = simpledialog.askstring("Take Quiz", "Enter course ID:")
       if course_id:
           quizzes = db.collection("quizzes").document(course_id).get().to_dict()
           if quizzes:
               # For simplicity, take the first available quiz
               quiz_data = quizzes
               self.start_quiz(quiz_data)
           else:
               messagebox.showinfo("Info", "No quizzes available for this course.")
  
   def start_quiz(self, quiz_data):
       self.clear_frame()
       self.quiz_frame = tk.Frame(self.master)
       self.quiz_frame.pack(pady=20)
      
       self.quiz_data = quiz_data
       self.current_question_index = 0
       self.score = 0
      
       tk.Label(self.quiz_frame, text=quiz_data["quiz_title"], font=("Helvetica", 16)).pack(pady=10)
      
       self.question_label = tk.Label(self.quiz_frame, text="", wraplength=400, justify="left")
       self.question_label.pack(pady=10)
      
       self.answer_entry = tk.Entry(self.quiz_frame, width=50)
       self.answer_entry.pack(pady=5)
      
       tk.Button(self.quiz_frame, text="Next", command=self.next_question, width=20).pack(pady=5)
      
       self.show_question()
  
   def show_question(self):
       questions = self.quiz_data["questions"]
       if self.current_question_index < len(questions):
           current_q = questions[self.current_question_index]["question"]
           self.question_label.config(text=f"Q{self.current_question_index + 1}: {current_q}")
           self.answer_entry.delete(0, tk.END)
       else:
           self.finish_quiz()
  
   def next_question(self):
       questions = self.quiz_data["questions"]
       current_q = questions[self.current_question_index]
       user_answer = self.answer_entry.get().strip().lower()
       correct_answer = current_q["answer"].strip().lower()
       if user_answer == correct_answer:
           self.score += 1
       self.current_question_index += 1
       self.show_question()
  
   def finish_quiz(self):
       self.clear_frame()
       result_frame = tk.Frame(self.master)
       result_frame.pack(pady=20)
       total_questions = len(self.quiz_data["questions"])
       tk.Label(result_frame, text=f"Quiz Completed! Your score: {self.score}/{total_questions}", font=("Helvetica", 16)).pack(pady=10)
       # Save grade to Firebase (structure: student_grades/{student_id})
       student_id = auth.current_user['localId']
       db.collection("student_grades").document(student_id).set({
           "quiz_title": self.quiz_data["quiz_title"],
           "score": self.score,
           "total": total_questions
       })
       tk.Button(result_frame, text="Back to Dashboard", command=self.show_student_dashboard, width=20).pack(pady=5)


def main2():
   root = tk.Tk()
   app = QuizApp(root)
   root.mainloop()


if __name__ == "__main__":
   main2()

