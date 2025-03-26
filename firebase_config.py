import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    
    try:
        if service_account_json:
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
        else:
            service_account_key_path = os.getenv("QUIZPROJECT_SERVICE_ACCOUNT_KEY", "path/to/serviceAccountKey.json")
            if not os.path.exists(service_account_key_path):
                raise FileNotFoundError(f"Service account key file not found: {service_account_key_path}")
            cred = credentials.Certificate(service_account_key_path)

        firebase_project_id = os.getenv("QUIZPROJECT_PROJECT_ID", "your-default-project-id")
        firebase_admin.initialize_app(cred, {"projectId": firebase_project_id})
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON in FIREBASE_SERVICE_ACCOUNT") from e

# Firestore client
db = firestore.client()
