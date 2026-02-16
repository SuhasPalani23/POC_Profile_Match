from flask import Blueprint, request, jsonify
from models.user import User
from config import Config
import jwt
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.find_by_id(data['user_id'])
            
            if not current_user:
                return jsonify({"error": "User not found"}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    skills = data.get('skills', [])
    bio = data.get('bio', '')
    
    if not email or not password or not name:
        return jsonify({"error": "Email, password, and name are required"}), 400
    
    user = User.create(email, password, name, skills, bio)
    
    if not user:
        return jsonify({"error": "User already exists"}), 409
    
    # Remove password from response
    if 'password' in user:
        del user['password']
    
    # Generate token
    token = jwt.encode({
        'user_id': user['_id'],
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }, Config.SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        "message": "User created successfully",
        "user": user,
        "token": token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    user = User.find_by_email(email)
    
    if not user or not User.verify_password(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Remove password from response
    if 'password' in user:
        del user['password']
    
    # Generate token
    token = jwt.encode({
        'user_id': user['_id'],
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }, Config.SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        "message": "Login successful",
        "user": user,
        "token": token
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    if 'password' in current_user:
        del current_user['password']
    return jsonify({"user": current_user}), 200