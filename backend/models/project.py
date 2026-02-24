from pymongo import MongoClient
from config import Config
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
projects_collection = db['projects']

class Project:
    @staticmethod
    def create(founder_id, title, description, required_skills=None):
        project = {
            "founder_id": founder_id,
            "title": title,
            "description": description,
            "required_skills": required_skills or [],
            "live": False,
            "status": "pending",
            "collaboration_requests": [],
            "cached_matches": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = projects_collection.insert_one(project)
        project['_id'] = str(result.inserted_id)
        return project

    @staticmethod
    def find_by_id(project_id):
        if not project_id or project_id == 'undefined' or project_id == 'null':
            return None

        try:
            project = projects_collection.find_one({"_id": ObjectId(project_id)})
            if project:
                project['_id'] = str(project['_id'])
            return project
        except Exception as e:
            print(f"Error finding project by ID '{project_id}': {e}")
            return None

    @staticmethod
    def find_by_founder(founder_id):
        projects = list(projects_collection.find({"founder_id": founder_id}))
        for project in projects:
            project['_id'] = str(project['_id'])
        return projects

    @staticmethod
    def update_status(project_id, live=True, status="approved"):
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"live": live, "status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    @staticmethod
    def add_collaboration_request(project_id, candidate_id, message=""):
        request = {
            "candidate_id": candidate_id,
            "message": message,
            "status": "pending",
            "created_at": datetime.utcnow()
        }

        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$push": {"collaboration_requests": request}}
        )
        return result.modified_count > 0

    @staticmethod
    def cache_matches(project_id, matches):
        """Cache match results so they are consistent on page refresh."""
        result = projects_collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {
                "cached_matches": matches,
                "matches_cached_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    @staticmethod
    def get_all_live_projects():
        projects = list(projects_collection.find({"live": True}))
        for project in projects:
            project['_id'] = str(project['_id'])
        return projects