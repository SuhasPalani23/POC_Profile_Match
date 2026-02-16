from pymongo import MongoClient
from config import Config
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
collaborations_collection = db['collaborations']

class Collaboration:
    @staticmethod
    def create_request(project_id, founder_id, candidate_id, message=""):
        """Create a collaboration request"""
        collaboration = {
            "project_id": project_id,
            "founder_id": founder_id,
            "candidate_id": candidate_id,
            "message": message,
            "status": "pending",  # pending, accepted, rejected
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "accepted_at": None
        }
        
        result = collaborations_collection.insert_one(collaboration)
        collaboration['_id'] = str(result.inserted_id)
        return collaboration
    
    @staticmethod
    def find_by_id(collaboration_id):
        """Find collaboration by ID"""
        collab = collaborations_collection.find_one({"_id": ObjectId(collaboration_id)})
        if collab:
            collab['_id'] = str(collab['_id'])
        return collab
    
    @staticmethod
    def find_by_candidate(candidate_id):
        """Get all collaboration requests for a candidate"""
        collabs = list(collaborations_collection.find({"candidate_id": candidate_id}))
        for collab in collabs:
            collab['_id'] = str(collab['_id'])
        return collabs
    
    @staticmethod
    def find_by_project(project_id):
        """Get all collaborations for a project"""
        collabs = list(collaborations_collection.find({"project_id": project_id}))
        for collab in collabs:
            collab['_id'] = str(collab['_id'])
        return collabs
    
    @staticmethod
    def find_pending_by_candidate(candidate_id):
        """Get pending requests for a candidate"""
        collabs = list(collaborations_collection.find({
            "candidate_id": candidate_id,
            "status": "pending"
        }))
        for collab in collabs:
            collab['_id'] = str(collab['_id'])
        return collabs
    
    @staticmethod
    def check_existing(project_id, candidate_id):
        """Check if collaboration already exists"""
        return collaborations_collection.find_one({
            "project_id": project_id,
            "candidate_id": candidate_id
        })
    
    @staticmethod
    def accept_request(collaboration_id):
        """Accept a collaboration request"""
        result = collaborations_collection.update_one(
            {"_id": ObjectId(collaboration_id)},
            {"$set": {
                "status": "accepted",
                "accepted_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    @staticmethod
    def reject_request(collaboration_id):
        """Reject a collaboration request"""
        result = collaborations_collection.update_one(
            {"_id": ObjectId(collaboration_id)},
            {"$set": {
                "status": "rejected",
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_team_members(project_id):
        """Get all accepted team members for a project"""
        collabs = list(collaborations_collection.find({
            "project_id": project_id,
            "status": "accepted"
        }))
        for collab in collabs:
            collab['_id'] = str(collab['_id'])
        return collabs
    
    @staticmethod
    def leave_project(collaboration_id):
        """Member leaves the project"""
        result = collaborations_collection.update_one(
            {"_id": ObjectId(collaboration_id)},
            {"$set": {
                "status": "left",
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_user_projects(user_id):
        """Get all projects where user is a member"""
        collabs = list(collaborations_collection.find({
            "candidate_id": user_id,
            "status": "accepted"
        }))
        for collab in collabs:
            collab['_id'] = str(collab['_id'])
        return collabs