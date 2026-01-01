import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

# Generate a strong SECRET_KEY if not provided
# In production, set this in environment variable
default_secret = secrets.token_urlsafe(32)
SECRET_KEY = os.getenv('SECRET_KEY', default_secret)

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
