import os
import sys
import threading
from dotenv import load_dotenv
from flask import Flask

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import Config
from models.user import User
from routes.profile import _upsert_user_vector_bg, get_vector_service

def main():
    dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
    load_dotenv(dotenv_path)

    # We need a proper Flask app context context for MongoDB & Config to work if they rely on it
    # But usually User.find_by_id doesn't strictly need request context if connection is global.
    
    # Initialize the vector service once to check it
    print("Initializing Pinecone Vector Service...")
    vs = get_vector_service()
    if not vs:
        print("Error: Could not initialize VectorService")
        return
        
    print("\nFetching all existing users from MongoDB...")
    from pymongo import MongoClient
    client = MongoClient(Config.MONGODB_URI)
    db = client[Config.DB_NAME]
    users = list(db.users.find({}))
    
    print(f"Found {len(users)} users. Starting deep normalization and Pinecone sync...")
    
    success_count = 0
    fail_count = 0
    
    for i, user_doc in enumerate(users):
        uid = str(user_doc["_id"])
        email = user_doc.get("email", "No Email")
        print(f"[{i+1}/{len(users)}] Normalizing user {email} ({uid})...")
        
        try:
            # We explicitly call the blocking version of the upsert which we just edited locally
            _upsert_user_vector_bg(uid)
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to normalize {email}: {e}")
            fail_count += 1
            
    print(f"\n✅ Backfill Complete! Successfully normalized and updated {success_count} vectors in Pinecone.")
    if fail_count > 0:
        print(f"⚠️ Encountered errors on {fail_count} users.")

if __name__ == "__main__":
    main()
