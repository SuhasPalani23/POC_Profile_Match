import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from config import Config
import bcrypt
from datetime import datetime

def ingest_users():
    """Ingest users from JSON file into MongoDB"""
    
    # Connect to MongoDB
    client = MongoClient(Config.MONGODB_URI)
    db = client[Config.DB_NAME]
    users_collection = db['users']
    
    # Optional: Clear existing users
    # users_collection.delete_many({})
    
    # Read JSON file
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'TalentMatchDB_users.json')
    
    with open(json_file_path, 'r') as f:
        users_data = json.load(f)
    
    # Default password for all users
    default_password = "Test@123"
    hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
    
    inserted_count = 0
    skipped_count = 0
    
    for user_data in users_data:
        # Check if user already exists
        existing_user = users_collection.find_one({"email": user_data.get('email')})
        
        if existing_user:
            print(f"Skipping existing user: {user_data.get('email')}")
            skipped_count += 1
            continue
        
        # Prepare user document - MAP JSON FIELDS TO EXPECTED FIELDS
        user_doc = {
            "email": user_data.get('email', ''),
            "password": hashed_password,
            "name": user_data.get('full_name', ''),  # Map full_name to name
            "skills": user_data.get('skills', []),
            "bio": user_data.get('bio', ''),
            "role": user_data.get('user_role', 'user'),  # Map user_role to role
            "resume": user_data.get('resume', ''),
            "linkedin": "",
            "professional_title": user_data.get('professional_title', ''),  # Keep this for reference
            "experience_years": user_data.get('experience_years', 0),
            "founding_mindset_score": user_data.get('founding_mindset_score', 0),
            "location": user_data.get('location', ''),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert user
        users_collection.insert_one(user_doc)
        print(f"Inserted user: {user_doc['email']} ({user_doc['name']})")
        inserted_count += 1
    
    print(f"\n=== Ingestion Complete ===")
    print(f"Total users inserted: {inserted_count}")
    print(f"Total users skipped: {skipped_count}")
    print(f"Default password for all users: {default_password}")
    
    client.close()

if __name__ == "__main__":
    print("Starting data ingestion...")
    ingest_users()