import os
from dotenv import load_dotenv

_backend_dir = os.path.dirname(os.path.abspath(__file__))
_root_env = os.path.abspath(os.path.join(_backend_dir, "..", ".env"))
# Always load the repo-level .env regardless of cwd.
load_dotenv(_root_env, override=True)

class Config:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'TalentMatchDB')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    IS_PRODUCTION = FLASK_ENV == 'production'
    PORT = int(os.getenv('PORT', '5001'))
    HOST = os.getenv('HOST', '0.0.0.0')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    FRONTEND_URLS = [url.strip() for url in os.getenv('FRONTEND_URLS', FRONTEND_URL).split(',') if url.strip()]
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(10 * 1024 * 1024)))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', '60'))
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '120'))
    RATE_LIMIT_AUTH_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_AUTH_WINDOW_SECONDS', '60'))
    RATE_LIMIT_AUTH_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_AUTH_MAX_REQUESTS', '40'))
    JWT_EXPIRATION_HOURS = 24
    MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB
    RESUME_UPLOAD_FOLDER = 'data/resumes'

    # Pinecone (replaces FAISS — shared cloud index visible to all devs/servers)
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'talent-match')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
    LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
    LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:5001/api/auth/linkedin/callback')
