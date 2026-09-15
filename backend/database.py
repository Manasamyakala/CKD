"""
database.py
MongoDB Compass Integration for NefroAI.
Connects to local MongoDB instance at mongodb://localhost:27017.
Manages:
- User Authentication (Login, Register, Salted Password Hash, Session)
- Patient Clinical Records & History (Inputs, CKD prediction, tablets, diet, yoga)
- Aggregated Clinical Statistics
"""

import os
import re
import hashlib
import secrets
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "nefroai_ckd"

class DatabaseManager:
    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2500)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            
            # Setup indices
            self.db.users.create_index([("username", ASCENDING)], unique=True)
            self.db.patient_records.create_index([("username", ASCENDING), ("created_at", DESCENDING)])
            print(f"[MongoDB] Successfully connected to {self.uri} -> {self.db_name}")
        except Exception as e:
            print(f"[MongoDB Connection Warning]: {e}. Operating in graceful fallback mode.")
            self.client = None
            self.db = None

    def is_connected(self):
        if not self.client:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

    @staticmethod
    def _hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((salt + password).encode("utf-8"))
        pwd_hash = hash_obj.hexdigest()
        return f"{salt}:{pwd_hash}"

    @staticmethod
    def _verify_password(password, stored_hash):
        try:
            salt, orig_hash = stored_hash.split(":")
            hash_obj = hashlib.sha256((salt + password).encode("utf-8"))
            return hash_obj.hexdigest() == orig_hash
        except Exception:
            return False

    def register_user(self, username, password, email="", full_name="", role="patient"):
        """
        Registers a new user into MongoDB 'users' collection with validations:
        - Username: Alphabetic letters only (no numbers)
        - Full Name: Alphabetic letters and spaces only (no numbers)
        - Email: Must end with @gmail.com or @gamil.com
        """
        if not self.is_connected():
            return False, "Database not connected. Please ensure MongoDB is running at mongodb://localhost:27017."
            
        username_clean = username.strip()
        full_name_clean = full_name.strip()
        email_clean = email.strip().lower()

        # 1. Username validation: Alphabetic characters only (no numerics)
        if not username_clean:
            return False, "Username cannot be empty."
        if not re.match(r"^[a-zA-Z]+$", username_clean):
            return False, "Username must contain only alphabets (no numbers or special characters)."
        if len(username_clean) < 3:
            return False, "Username must be at least 3 letters long."

        # 2. Full name validation: Alphabetic characters only (no numerics)
        if not full_name_clean:
            return False, "Full name cannot be empty."
        if not re.match(r"^[a-zA-Z\s]+$", full_name_clean):
            return False, "Full name must contain only alphabets (no numbers or symbols)."
        if len(full_name_clean) < 2:
            return False, "Full name must be at least 2 letters long."

        # 3. Email validation: Must end with @gmail.com or @gamil.com
        if not (email_clean.endswith("@gmail.com") or email_clean.endswith("@gamil.com")):
            return False, "Email must end with @gmail.com (or @gamil.com)."
        if not re.match(r"^[a-zA-Z0-9._%+-]+@(gmail|gamil)\.com$", email_clean):
            return False, "Please provide a valid email format ending with @gmail.com (or @gamil.com)."

        # 4. Password validation
        if len(password) < 4:
            return False, "Password must be at least 4 characters long."

        pwd_encoded = self._hash_password(password)
        user_doc = {
            "username": username_clean.lower(),
            "password_hash": pwd_encoded,
            "email": email_clean,
            "full_name": full_name_clean,
            "role": role,
            "created_at": datetime.now()
        }

        try:
            self.db.users.insert_one(user_doc)
            return True, "User registered successfully!"
        except DuplicateKeyError:
            return False, f"Username '{username_clean.lower()}' already exists. Please choose another username."
        except Exception as e:
            return False, f"Registration failed: {e}"

    def authenticate_user(self, username, password):
        """
        Authenticates a user from MongoDB.
        Returns (success: bool, user_doc or error_msg: str)
        """
        if not self.is_connected():
            # Graceful fallback for local development if MongoDB connection drops
            return False, "MongoDB server is offline. Please check mongodb://localhost:27017."

        username = username.strip().lower()
        user = self.db.users.find_one({"username": username})
        if not user:
            return False, "Invalid username or user does not exist."

        if self._verify_password(password, user.get("password_hash", "")):
            return True, {
                "username": user["username"],
                "email": user.get("email", ""),
                "full_name": user.get("full_name", user["username"]),
                "role": user.get("role", "patient")
            }
        else:
            return False, "Invalid password. Please try again."

    def save_patient_record(self, record_data):
        """
        Saves prediction, input biomarkers, tablets, and personalized recommendations.
        """
        if not self.is_connected():
            return None, "Database offline."

        record = {
            "record_id": secrets.token_hex(8),
            "username": record_data.get("username", "anonymous"),
            "patient_name": record_data.get("patient_name", "Patient"),
            "age": record_data.get("age", 50),
            "gender": record_data.get("gender", "Male"),
            "input_parameters": record_data.get("input_parameters", {}),
            "prediction": record_data.get("prediction", {}),
            "prescribed_tablets": record_data.get("prescribed_tablets", []),
            "diet_plan": record_data.get("diet_plan", {}),
            "yoga_program": record_data.get("yoga_program", []),
            "exercise_plan": record_data.get("exercise_plan", {}),
            "telemetry": record_data.get("telemetry", {}),
            "created_at": datetime.now(),
            "formatted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            result = self.db.patient_records.insert_one(record)
            return record["record_id"], "Record saved to MongoDB!"
        except Exception as e:
            return None, f"Failed to save record: {e}"

    def get_patient_records(self, username=None, limit=50):
        """
        Retrieves patient assessment history.
        """
        if not self.is_connected():
            return []

        query = {}
        if username and username != "admin":
            query["username"] = username

        try:
            records = list(self.db.patient_records.find(query, {"_id": 0}).sort("created_at", DESCENDING).limit(limit))
            return records
        except Exception as e:
            print(f"Error fetching records: {e}")
            return []

    def get_database_stats(self):
        """
        Returns stats for admin/overview dashboard.
        """
        if not self.is_connected():
            return {"connected": False, "total_users": 0, "total_records": 0, "ckd_cases": 0}

        try:
            total_users = self.db.users.count_documents({})
            total_records = self.db.patient_records.count_documents({})
            ckd_cases = self.db.patient_records.count_documents({"prediction.is_ckd": True})
            return {
                "connected": True,
                "database_name": self.db_name,
                "mongo_uri": self.uri,
                "total_users": total_users,
                "total_records": total_records,
                "ckd_cases": ckd_cases,
                "non_ckd_cases": total_records - ckd_cases
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

# Singleton instance
db_manager = DatabaseManager()

if __name__ == "__main__":
    print("=== Testing MongoDB Integration ===")
    print("Connection Status:", db_manager.is_connected())
    stats = db_manager.get_database_stats()
    print("Database Stats:", stats)
    
    # Test registration & authentication
    test_user = "demo_doctor"
    test_pass = "nefro123"
    db_manager.register_user(test_user, test_pass, "doctor@hospital.org", "Dr. Demo Physician", "clinician")
    success, auth_res = db_manager.authenticate_user(test_user, test_pass)
    print(f"Auth Test for '{test_user}': {success} -> {auth_res}")
