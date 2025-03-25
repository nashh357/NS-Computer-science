import firebase_admin
from firebase_admin import credentials, firestore

# Path to your service account key JSON file
service_account_key_path = "quizproject-a6230-firebase-adminsdk-fbsvc-267213700c.json"

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_key_path)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()