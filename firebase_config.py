import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    # Try to get service account info from environment variable first
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    if service_account_json:
        # Parse the JSON string from environment variable
        service_account_info = json.loads(service_account_json)
        cred = credentials.Certificate(service_account_info)
    else:
        # Fallback to local file for development
        service_account_key_path = os.getenv("QUIZPROJECT_SERVICE_ACCOUNT_KEY", "Path/to/serviceAccountKey.json")
        cred = credentials.Certificate(service_account_key_path)
    
    firebase_project_id = os.getenv("QUIZPROJECT_PROJECT_ID")
    firebase_admin.initialize_app(cred, {"projectId": firebase_project_id})

# Firestore client
db = firestore.client()
