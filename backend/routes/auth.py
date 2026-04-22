from flask import Blueprint, request
from models.user import User
from config import Config
from services.vector_service import VectorService
import jwt
from datetime import datetime, timedelta
from functools import wraps
from utils.api_response import api_error, api_success, validation_error
from utils.validation import validate_required_fields
from services.background_tasks import enqueue

auth_bp = Blueprint('auth', __name__)
vector_service = None
vector_service_init_attempted = False


def _database_unavailable_response(exc: Exception):
    print(f"[Auth] Database unavailable: {exc}")
    return api_error(
        "DB_UNAVAILABLE",
        "Database connection is temporarily unavailable",
        503,
        {"service": "mongo"},
    )


def get_vector_service():
    global vector_service, vector_service_init_attempted
    if vector_service is not None:
        return vector_service
    if vector_service_init_attempted:
        return None
    vector_service_init_attempted = True
    try:
        vector_service = VectorService()
    except Exception as exc:
        print(f"[Auth] Vector service unavailable: {exc}")
        vector_service = None
    return vector_service


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return api_error("TOKEN_MISSING", "Token is missing", 401)
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.find_by_id(data['user_id'])
            
            if not current_user:
                return api_error("USER_NOT_FOUND", "User not found", 401)
        except jwt.ExpiredSignatureError:
            return api_error("TOKEN_EXPIRED", "Token has expired", 401)
        except jwt.InvalidTokenError:
            return api_error("INVALID_TOKEN", "Invalid token", 401)
        except Exception as exc:
            return _database_unavailable_response(exc)
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def _vectorize_new_user(user: dict):
    service = get_vector_service()
    if service is None:
        return
    try:
        service.upsert_user(user)
        print(f"[Auth] Vectorized new user {user['_id']}")
    except Exception as e:
        print(f"[Auth] Warning: Failed to vectorize new user {user['_id']}: {e}")


def _vectorize_user_by_id(user_id: str):
    """Re-index a user by ID (used after profile changes in auth routes)."""
    service = get_vector_service()
    if service is None:
        return
    try:
        user = User.find_by_id(user_id)
        if user:
            service.upsert_user(user)
            print(f"[Auth] Re-indexed user {user_id}")
    except Exception as e:
        print(f"[Auth] Warning: Failed to re-index user {user_id}: {e}")


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["name", "email", "password"])
    if not validation["is_valid"]:
        return validation_error(
            "Name, email, and password are required",
            {"missing_fields": validation["missing_fields"]},
        )
    
    email = (data.get('email') or '').strip()
    password = data.get('password')
    name = (data.get('name') or '').strip()
    skills = data.get('skills', [])
    bio = data.get('bio', '')
    
    try:
        user = User.create(email, password, name, skills, bio)
    except Exception as exc:
        return _database_unavailable_response(exc)
    
    if not user:
        return api_error("USER_EXISTS", "User already exists", 409)

    # Vectorize in background — signup doesn't wait for Pinecone
    enqueue(_vectorize_new_user, user)

    # Remove password from response
    if 'password' in user:
        del user['password']
    
    # Generate token
    token = jwt.encode({
        'user_id': user['_id'],
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }, Config.SECRET_KEY, algorithm="HS256")
    
    return api_success({
        "user": user,
        "token": token
    }, message="User created successfully", code="USER_CREATED", status=201)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["email", "password"])
    if not validation["is_valid"]:
        return validation_error(
            "Email and password are required",
            {"missing_fields": validation["missing_fields"]},
        )

    email = data.get('email')
    password = data.get('password')
    
    try:
        user = User.find_by_email(email)
    except Exception as exc:
        return _database_unavailable_response(exc)
    
    if not user or not User.verify_password(user['password'], password):
        return api_error("INVALID_CREDENTIALS", "Invalid credentials", 401)
    
    # Remove password from response
    if 'password' in user:
        del user['password']
    
    # Generate token
    token = jwt.encode({
        'user_id': user['_id'],
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }, Config.SECRET_KEY, algorithm="HS256")
    
    return api_success({"user": user, "token": token}, message="Login successful", code="LOGIN_SUCCESS")


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    if 'password' in current_user:
        del current_user['password']
    return api_success({"user": current_user}, message="Current user fetched")


@auth_bp.route('/delete-account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    """Delete user account — removes from MongoDB, Pinecone, and GridFS."""
    from db import get_collection
    from bson.objectid import ObjectId

    user_id = current_user["_id"]

    # Remove from Pinecone
    vs = get_vector_service()
    if vs:
        try:
            vs.remove_user(user_id)
            print(f"[Auth] Removed user {user_id} from Pinecone")
        except Exception as e:
            print(f"[Auth] Warning: Failed to remove from Pinecone: {e}")

    # Remove resume from GridFS if exists
    if current_user.get("resume_file_id"):
        try:
            import gridfs
            from pymongo import MongoClient
            client = MongoClient(Config.MONGODB_URI)
            fs = gridfs.GridFS(client[Config.DB_NAME])
            fs.delete(ObjectId(current_user["resume_file_id"]))
        except Exception as e:
            print(f"[Auth] Warning: Failed to delete resume from GridFS: {e}")

    # Remove from MongoDB
    get_collection("users").delete_one({"_id": ObjectId(user_id)})

    # Clean up collaborations
    get_collection("collaborations").delete_many({
        "$or": [{"candidate_id": user_id}, {"founder_id": user_id}]
    })

    print(f"[Auth] Account deleted: {user_id} ({current_user.get('email', '')})")
    return api_success({"deleted": True}, message="Account deleted successfully")


