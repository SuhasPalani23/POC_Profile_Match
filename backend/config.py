import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'TalentMatchDB')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    IS_PRODUCTION = FLASK_ENV == 'production'
    PORT = int(os.getenv('PORT', '5001'))
    HOST = os.getenv('HOST', '0.0.0.0')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    FRONTEND_URLS = [url.strip() for url in os.getenv('FRONTEND_URLS', FRONTEND_URL).split(',') if url.strip()]
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(10 * 1024 * 1024)))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', '60'))
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '120'))
    RATE_LIMIT_AUTH_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_AUTH_WINDOW_SECONDS', '60'))
    RATE_LIMIT_AUTH_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_AUTH_MAX_REQUESTS', '20'))
    JWT_EXPIRATION_HOURS = 24
    MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB
    RESUME_UPLOAD_FOLDER = 'data/resumes'

    # Pinecone (replaces FAISS — shared cloud index visible to all devs/servers)
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'talent-match')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
