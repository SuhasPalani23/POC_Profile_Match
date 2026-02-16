from datetime import datetime, timedelta
from pymongo import MongoClient
from config import Config
import secrets
import jwt

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DB_NAME]
sessions_collection = db['sessions']

class SessionManager:
    """Manage user sessions with MongoDB"""
    
    @staticmethod
    def create_session(user_id, ip_address=None, user_agent=None):
        """Create a new session for user"""
        session_token = secrets.token_urlsafe(32)
        
        session = {
            'user_id': user_id,
            'session_token': session_token,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
            'active': True
        }
        
        sessions_collection.insert_one(session)
        return session_token
    
    @staticmethod
    def get_session(session_token):
        """Get session by token"""
        return sessions_collection.find_one({
            'session_token': session_token,
            'active': True,
            'expires_at': {'$gt': datetime.utcnow()}
        })
    
    @staticmethod
    def update_activity(session_token):
        """Update last activity timestamp"""
        sessions_collection.update_one(
            {'session_token': session_token},
            {'$set': {'last_activity': datetime.utcnow()}}
        )
    
    @staticmethod
    def invalidate_session(session_token):
        """Invalidate a session"""
        sessions_collection.update_one(
            {'session_token': session_token},
            {'$set': {'active': False}}
        )
    
    @staticmethod
    def invalidate_all_user_sessions(user_id):
        """Invalidate all sessions for a user"""
        sessions_collection.update_many(
            {'user_id': user_id},
            {'$set': {'active': False}}
        )
    
    @staticmethod
    def get_active_sessions(user_id):
        """Get all active sessions for a user"""
        return list(sessions_collection.find({
            'user_id': user_id,
            'active': True,
            'expires_at': {'$gt': datetime.utcnow()}
        }))
    
    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions"""
        sessions_collection.delete_many({
            'expires_at': {'$lt': datetime.utcnow()}
        })
    
    @staticmethod
    def extend_session(session_token, hours=None):
        """Extend session expiration"""
        hours = hours or Config.JWT_EXPIRATION_HOURS
        new_expiry = datetime.utcnow() + timedelta(hours=hours)
        
        sessions_collection.update_one(
            {'session_token': session_token},
            {'$set': {
                'expires_at': new_expiry,
                'last_activity': datetime.utcnow()
            }}
        )
    
    @staticmethod
    def get_session_info(session_token):
        """Get detailed session information"""
        session = SessionManager.get_session(session_token)
        if not session:
            return None
        
        return {
            'user_id': session['user_id'],
            'ip_address': session.get('ip_address'),
            'user_agent': session.get('user_agent'),
            'created_at': session['created_at'],
            'last_activity': session['last_activity'],
            'expires_at': session['expires_at'],
            'time_remaining': (session['expires_at'] - datetime.utcnow()).total_seconds()
        }

# Initialize session cleanup on import
# In production, use a scheduler like Celery or APScheduler
def init_session_cleanup():
    """Initialize periodic session cleanup"""
    import threading
    import time
    
    def cleanup_task():
        while True:
            time.sleep(3600)  # Run every hour
            SessionManager.cleanup_expired_sessions()
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

# Auto-start cleanup
init_session_cleanup()