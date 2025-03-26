from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables from .env
load_dotenv()

# Get environment variables
service_account_key_path = os.getenv("QUIZPROJECT_SERVICE_ACCOUNT_KEY")
firebase_project_id = os.getenv("QUIZPROJECT_PROJECT_ID")

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_key_path)
    firebase_admin.initialize_app(cred, {"projectId": firebase_project_id})

# Firestore client
db = firestore.client()
# Removed hardcoded path to the service account key
