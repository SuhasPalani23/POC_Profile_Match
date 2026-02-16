from pymongo import MongoClient
from config import Config
import bcrypt
from datetime import datetime

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
users_collection = db['users']

class User:
    @staticmethod
    def create(email, password, name, skills=None, bio="", role="user"):
        if users_collection.find_one({"email": email}):
            return None
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = {
            "email": email,
            "password": hashed_password,
            "name": name,
            "skills": skills or [],
            "bio": bio,
            "role": role,
            "resume": "",
            "resume_parsed": False,
            "linkedin": "",
            "professional_title": "",
            "experience_years": 0,
            "location": "",
            "founding_mindset_score": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = users_collection.insert_one(user)
        user['_id'] = str(result.inserted_id)
        return user
    
    @staticmethod
    def find_by_email(email):
        user = users_collection.find_one({"email": email})
        if user:
            user['_id'] = str(user['_id'])
        return user
    
    @staticmethod
    def find_by_id(user_id):
        from bson.objectid import ObjectId
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
        return user
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)
    
    @staticmethod
    def update_role(user_id, new_role):
        from bson.objectid import ObjectId
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": new_role, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def update_profile(user_id, update_data):
        """Update user profile fields"""
        from bson.objectid import ObjectId
        
        update_data['updated_at'] = datetime.utcnow()
        
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_all_users(exclude_user_id=None, role_filter=None):
        query = {}
        if exclude_user_id:
            from bson.objectid import ObjectId
            query["_id"] = {"$ne": ObjectId(exclude_user_id)}
        if role_filter:
            query["role"] = role_filter
        
        users = list(users_collection.find(query))
        for user in users:
            user['_id'] = str(user['_id'])
            if 'password' in user:
                del user['password']
        return users