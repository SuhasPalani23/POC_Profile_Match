from pymongo import MongoClient
from config import Config
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
messages_collection = db['messages']

class Message:
    @staticmethod
    def create(project_id, sender_id, sender_name, message_text):
        """Create a new chat message"""
        message = {
            "project_id": project_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "message": message_text,
            "created_at": datetime.utcnow(),
            "read_by": []  # Array of user_ids who have read the message
        }
        
        result = messages_collection.insert_one(message)
        message['_id'] = str(result.inserted_id)
        return message
    
    @staticmethod
    def get_project_messages(project_id, limit=100):
        """Get messages for a project"""
        messages = list(messages_collection.find(
            {"project_id": project_id}
        ).sort("created_at", -1).limit(limit))
        
        # Reverse to show oldest first
        messages.reverse()
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        return messages
    
    @staticmethod
    def mark_as_read(message_id, user_id):
        """Mark message as read by user"""
        result = messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$addToSet": {"read_by": user_id}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_unread_count(project_id, user_id):
        """Get unread message count for a user in a project"""
        count = messages_collection.count_documents({
            "project_id": project_id,
            "sender_id": {"$ne": user_id},
            "read_by": {"$ne": user_id}
        })
        return count
    
    @staticmethod
    def delete_message(message_id):
        """Delete a message"""
        result = messages_collection.delete_one({"_id": ObjectId(message_id)})
        return result.deleted_count > 0