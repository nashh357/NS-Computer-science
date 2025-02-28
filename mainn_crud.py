import firebase_admin
from firebase_admin import credentials, firestore




# Initialize Firebase with service account credentials
cred = credentials.Certificate("quizly.json")
firebase_admin.initialize_app(cred)


# Get Firestore client
db = firestore.client()




# 1. CRUD Operations - Add data
def add_data():
   employees = [
       {"name": "Alice Johnson", "email": "alice.johnson@example.com", "age": 22},
       {"name": "Bob Smith", "email": "bob.smith@example.com", "age": 30},
       {"name": "Charlie Brown", "email": "charlie.brown@example.com", "age": 25},
       {"name": "David Wilson", "email": "david.wilson@example.com", "age": 28},
       {"name": "Eva Green", "email": "eva.green@example.com", "age": 35},
       {"name": "Frank White", "email": "frank.white@example.com", "age": 40},
       {"name": "Grace Lee", "email": "grace.lee@example.com", "age": 27},
       {"name": "Hannah Scott", "email": "hannah.scott@example.com", "age": 32},
       {"name": "Ian Black", "email": "ian.black@example.com", "age": 29},
       {"name": "Jackie Brown", "email": "jackie.brown@example.com", "age": 24},
       {"name": "Karen Davis", "email": "karen.davis@example.com", "age": 31},
       {"name": "Liam Turner", "email": "liam.turner@example.com", "age": 26},
       {"name": "Mia Clark", "email": "mia.clark@example.com", "age": 34},
       {"name": "Noah Lewis", "email": "noah.lewis@example.com", "age": 28},
       {"name": "Olivia Walker", "email": "olivia.walker@example.com", "age": 30},
       {"name": "Paul Harris", "email": "paul.harris@example.com", "age": 33},
       {"name": "Quinn Martinez", "email": "quinn.martinez@example.com", "age": 29},
       {"name": "Rachel Young", "email": "rachel.young@example.com", "age": 27},
       {"name": "Sam King", "email": "sam.king@example.com", "age": 31},
       {"name": "Tina Wright", "email": "tina.wright@example.com", "age": 32},
       {"name": "Uma Baker", "email": "uma.baker@example.com", "age": 28}
   ]


   try:
       for i, employee in enumerate(employees):
           # Add a document with a generated ID
           db.collection("employee").add(employee)


           # Add a document with a custom ID
           # custom_id = f"employee_{i+1}"
           # db.collection("employee").document(custom_id).set(employee)
       print("Data added successfully.")
   except Exception as e:
       print(f"An error occurred: {e}")


# Call the function to add data
add_data()


# 2. CRUD Operations - Read data
# Retrieve a document by ID
def read_data():
   try:
       doc_ref = db.collection("employee").document("employee_1")
       doc = doc_ref.get()
       if doc.exists:
           print(f"Document data: {doc.to_dict()}")
       else:
           print("No such document!")
   except Exception as e:
       print(f"An error occurred: {e}")


# Call the function to read data
read_data()


# 3. Update a document
try:
   doc_ref = db.collection("employee").document("employee_1")
   doc_ref.update({"age": 23})
   print("Document updated successfully.")
except Exception as e:
   print(f"An error occurred: {e}")


# 4. Delete a document
try:
   doc_ref = db.collection("employee").document("employee_1")
   doc_ref.delete()
   print("Document deleted successfully.")
except Exception as e:
   print(f"An error occurred: {e}")


# 5. Query documents
try:
   docs = db.collection("employee").where("age", ">", 20).stream()
   for doc in docs:
       print(f"{doc.id} => {doc.to_dict()}")
except Exception as e:
   print(f"An error occurred: {e}")


# 6. List all documents in a collection
try:
   docs = db.collection("employee").stream()
   for doc in docs:
       print(f"{doc.id} => {doc.to_dict()}")
except Exception as e:
   print(f"An error occurred: {e}")
# 7. List all collections
try:
   collections = db.collections()
   for collection in collections:
       print(f"Collection: {collection.id}")
except Exception as e:
   print(f"An error occurred: {e}")


db.close()









