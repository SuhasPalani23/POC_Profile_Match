import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'TalentMatchDB')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    FAISS_INDEX_PATH = 'data/faiss_index'
    JWT_EXPIRATION_HOURS = 24
    MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB
    RESUME_UPLOAD_FOLDER = 'data/resumes'