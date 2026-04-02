from flask import Blueprint, request, redirect
from models.user import User
from config import Config
from services.vector_service import VectorService
import jwt
import requests as http_requests
import urllib.parse
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


# ------------------------------------------------------------------
# LinkedIn OAuth 2.0
# ------------------------------------------------------------------

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/userinfo"

LINKEDIN_SCOPES = "openid profile email"


@auth_bp.route('/linkedin/consent-url', methods=['POST'])
@token_required
def linkedin_consent_url(current_user):
    """Return the LinkedIn OAuth consent URL for the frontend to redirect to."""
    if not Config.LINKEDIN_CLIENT_ID or not Config.LINKEDIN_CLIENT_SECRET:
        return api_error("CONFIG_ERROR", "LinkedIn OAuth is not configured", 500)

    # Encode the user's JWT token in state so we can link back after callback
    state = jwt.encode({
        'user_id': current_user['_id'],
        'exp': datetime.utcnow() + timedelta(minutes=10)
    }, Config.SECRET_KEY, algorithm="HS256")

    params = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': Config.LINKEDIN_CLIENT_ID,
        'redirect_uri': Config.LINKEDIN_REDIRECT_URI,
        'scope': LINKEDIN_SCOPES,
        'state': state,
    })

    consent_url = f"{LINKEDIN_AUTH_URL}?{params}"
    return api_success({"consentUrl": consent_url}, message="LinkedIn consent URL generated")


@auth_bp.route('/linkedin/callback', methods=['GET'])
def linkedin_callback():
    """LinkedIn redirects here after user consents. Exchange code for token, then redirect to frontend."""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    frontend_url = Config.FRONTEND_URLS[0] if Config.FRONTEND_URLS else 'http://localhost:3000'

    if error:
        return redirect(f"{frontend_url}/profile/edit?linkedin_error={urllib.parse.quote(error)}")

    if not code or not state:
        return redirect(f"{frontend_url}/profile/edit?linkedin_error=missing_code")

    # Verify state token
    try:
        state_data = jwt.decode(state, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = state_data['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return redirect(f"{frontend_url}/profile/edit?linkedin_error=invalid_state")

    # Exchange code for access token
    try:
        token_resp = http_requests.post(LINKEDIN_TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': Config.LINKEDIN_REDIRECT_URI,
            'client_id': Config.LINKEDIN_CLIENT_ID,
            'client_secret': Config.LINKEDIN_CLIENT_SECRET,
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=15)

        if token_resp.status_code != 200:
            return redirect(f"{frontend_url}/profile/edit?linkedin_error=token_exchange_failed")

        token_data = token_resp.json()
        access_token = token_data.get('access_token')
    except Exception:
        return redirect(f"{frontend_url}/profile/edit?linkedin_error=token_exchange_failed")

    # ── Fetch identity from LinkedIn OpenID userinfo ──
    linkedin_email = ""
    linkedin_name = ""
    linkedin_sub = ""
    try:
        profile_resp = http_requests.get(LINKEDIN_PROFILE_URL, headers={
            'Authorization': f'Bearer {access_token}'
        }, timeout=10)
        if profile_resp.status_code == 200:
            li_profile = profile_resp.json()
            linkedin_email = li_profile.get('email', '')
            linkedin_name = li_profile.get('name', '')
            linkedin_sub = li_profile.get('sub', '')  # opaque member ID
            print(f"[linkedin_callback] Got identity: name={linkedin_name} email={linkedin_email} sub={linkedin_sub}")
    except Exception as e:
        print(f"[linkedin_callback] userinfo error: {e}")

    # ── Try LinkedIn v2 API to get vanity name (profile URL) ──
    linkedin_vanity_url = ""
    try:
        # Try /v2/me endpoint — may return vanityName depending on app permissions
        me_resp = http_requests.get("https://api.linkedin.com/v2/me", headers={
            'Authorization': f'Bearer {access_token}'
        }, timeout=10)
        if me_resp.status_code == 200:
            me_data = me_resp.json()
            vanity = me_data.get('vanityName', '')
            if vanity:
                linkedin_vanity_url = f"https://www.linkedin.com/in/{vanity}"
                print(f"[linkedin_callback] Got vanity URL: {linkedin_vanity_url}")
            else:
                print(f"[linkedin_callback] /v2/me returned no vanityName. Keys: {list(me_data.keys())}")
        else:
            print(f"[linkedin_callback] /v2/me returned {me_resp.status_code}")
    except Exception as e:
        print(f"[linkedin_callback] /v2/me error: {e}")

    # ── Store auth identity on user ──
    update_data = {
        'linkedinAuthed': True,
        'linkedinAuthedAt': datetime.utcnow(),
    }
    if linkedin_email:
        update_data['linkedinOAuthEmail'] = linkedin_email
    if linkedin_name:
        update_data['linkedinOAuthName'] = linkedin_name
    if linkedin_sub:
        update_data['linkedinOAuthSub'] = linkedin_sub
    if linkedin_vanity_url:
        # We found their actual profile URL — lock it immediately
        update_data['linkedinUrl'] = linkedin_vanity_url
        update_data['linkedin'] = linkedin_vanity_url

    User.update_profile(user_id, update_data)

    # Re-index in Pinecone so LinkedIn data is searchable
    enqueue(_vectorize_user_by_id, user_id)

    # Build redirect with whatever we found
    updated_user = User.find_by_id(user_id)
    final_url = linkedin_vanity_url
    if not final_url and updated_user:
        final_url = updated_user.get('linkedinUrl') or updated_user.get('linkedin') or ''

    redirect_params = 'linkedin_success=true'
    if final_url:
        redirect_params += f'&linkedin_url={urllib.parse.quote(final_url)}'
    if linkedin_name:
        redirect_params += f'&linkedin_name={urllib.parse.quote(linkedin_name)}'
    if linkedin_email:
        redirect_params += f'&linkedin_email={urllib.parse.quote(linkedin_email)}'

    return redirect(f"{frontend_url}/profile/edit?{redirect_params}")


@auth_bp.route('/linkedin/status', methods=['GET'])
@token_required
def linkedin_auth_status(current_user):
    """Check if the current user has authenticated with LinkedIn."""
    return api_success({
        "linkedinAuthed": bool(current_user.get('linkedinAuthed')),
        "linkedinAuthedAt": str(current_user.get('linkedinAuthedAt', '')),
        "linkedinOAuthEmail": current_user.get('linkedinOAuthEmail', ''),
        "linkedinOAuthName": current_user.get('linkedinOAuthName', ''),
        "linkedinUrl": current_user.get('linkedinUrl', '') or current_user.get('linkedin', ''),
    }, message="LinkedIn auth status")


@auth_bp.route('/linkedin/disconnect', methods=['POST'])
@token_required
def linkedin_disconnect(current_user):
    """Remove ALL LinkedIn data — full clean slate for fresh re-authentication."""
    from db import get_collection
    from bson.objectid import ObjectId
    get_collection("users").update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$unset": {
            "linkedinAuthed": "",
            "linkedinAccessToken": "",
            "linkedinAuthedAt": "",
            "linkedinOAuthEmail": "",
            "linkedinOAuthName": "",
            "linkedinUrl": "",
            "linkedin": "",
            "linkedin_scraped": "",
        }}
    )
    # Re-index to remove stale LinkedIn data from Pinecone
    enqueue(_vectorize_user_by_id, current_user["_id"])
    return api_success({"linkedinAuthed": False}, message="LinkedIn disconnected — all LinkedIn data removed")
