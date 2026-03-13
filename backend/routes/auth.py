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
try:
    vector_service = VectorService()
except Exception as exc:
    vector_service = None
    print(f"[Auth] Vector service unavailable at startup: {exc}")


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
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def _vectorize_new_user(user: dict):
    if vector_service is None:
        return
    try:
        vector_service.upsert_user(user)
        print(f"[Auth] Vectorized new user {user['_id']}")
    except Exception as e:
        print(f"[Auth] Warning: Failed to vectorize new user {user['_id']}: {e}")


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}
    validation = validate_required_fields(data, ["email", "password", "name"])
    if not validation["is_valid"]:
        return validation_error(
            "Email, password, and name are required",
            {"missing_fields": validation["missing_fields"]},
        )
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    skills = data.get('skills', [])
    bio = data.get('bio', '')
    
    user = User.create(email, password, name, skills, bio)
    
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
    
    user = User.find_by_email(email)
    
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
