import os
import json
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_firebase_credentials():
    """Get Firebase credentials from environment variables."""
    try:
        # Get credentials from environment variables
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        private_key = os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')

        if not all([project_id, private_key, client_email]):
            raise ValueError("Missing required Firebase credentials in environment variables")

        # Construct credentials dictionary
        creds = {
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
        
        return credentials.Certificate(creds)
    except Exception as e:
        raise Exception(f"Failed to load Firebase credentials: {str(e)}")

# Initialize Firebase
try:
    cred = get_firebase_credentials()
    firebase_app = initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    raise