from pymongo import MongoClient
from config import Config
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
messages_collection = db['messages']

class Message:
    @staticmethod
    def create(project_id, sender_id, sender_name, message_text, dm_recipient_id=None):
        """Create a new chat message (group or DM)"""
        message = {
            "project_id": project_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "message": message_text,
            "dm_recipient_id": dm_recipient_id,  # None = group message, else DM
            "created_at": datetime.utcnow(),
            "read_by": []
        }
        
        result = messages_collection.insert_one(message)
        message['_id'] = str(result.inserted_id)
        return message
    
    @staticmethod
    def get_project_messages(project_id, limit=100):
        """Get group messages for a project"""
        messages = list(messages_collection.find(
            {"project_id": project_id, "dm_recipient_id": None}
        ).sort("created_at", -1).limit(limit))
        
        messages.reverse()
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        return messages
    
    @staticmethod
    def get_dm_messages(project_id, user_a, user_b, limit=100):
        """Get DM messages between two users in a project context"""
        messages = list(messages_collection.find({
            "project_id": project_id,
            "$or": [
                {"sender_id": user_a, "dm_recipient_id": user_b},
                {"sender_id": user_b, "dm_recipient_id": user_a},
            ]
        }).sort("created_at", -1).limit(limit))
        
        messages.reverse()
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        return messages
    
    @staticmethod
    def mark_as_read(message_id, user_id):
        result = messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$addToSet": {"read_by": user_id}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_unread_count(project_id, user_id):
        count = messages_collection.count_documents({
            "project_id": project_id,
            "dm_recipient_id": None,
            "sender_id": {"$ne": user_id},
            "read_by": {"$ne": user_id}
        })
        return count
    
    @staticmethod
    def delete_message(message_id):
        result = messages_collection.delete_one({"_id": ObjectId(message_id)})
        return result.deleted_count > 0