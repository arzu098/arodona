import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"  # Look in backend root folder
load_dotenv(dotenv_path=env_path)

# Database Configuration
# For production, use the MONGODB_URL environment variable
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://bhoomi:bhoomi23@cluster0.wcbjoil.mongodb.net/arodona_db?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "arodona_db")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "60"))  # 1 hour by default

# Super Admin Configuration
SUPER_ADMIN_SECRET_KEY = os.getenv("SUPER_ADMIN_SECRET_KEY", "super-admin-secret-key-2024")

# API Configuration
API_TITLE = "Arodona Jewelry Backend"
API_VERSION = "1.0.0"

# Index management options
# When True, the app will drop an existing non-TTL `timestamp` index and recreate it
# as a TTL index on startup. Use with caution for production collections.
FORCE_RECREATE_TTL = os.getenv("FORCE_RECREATE_TTL", "false").lower() in ("1", "true", "yes")

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS Configuration for production
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3003", 
    "http://localhost:3004",
    "http://localhost:5173",
    "https://adorona-frontend.vercel.app",
    "https://adorona.vercel.app",
    "https://adorona-frontend.netlify.app",
    # Add your actual frontend deployment URLs here
]

# File Upload Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB