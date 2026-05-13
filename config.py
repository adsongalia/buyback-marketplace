import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

# Find the absolute path of the directory containing this file
basedir = os.path.abspath(os.path.dirname(__file__))
# Load the .env file from the project root (one level up from config.py)
project_root = os.path.abspath(os.path.join(basedir, os.pardir))
load_dotenv(os.path.join(project_root, '.env'))

class Config:
    """Set Flask configuration variables from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-secret-key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # NEW: Add engine options for serverless compatibility
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': NullPool
    }

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Supabase
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
