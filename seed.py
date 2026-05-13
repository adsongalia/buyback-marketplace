import requests
import os
import uuid
from dotenv import load_dotenv
# Explicitly load .env for standalone script execution
project_root = os.path.abspath(os.path.dirname(__file__)) # Corrected path
load_dotenv(os.path.join(project_root, '.env'))

from app import app, db # This line was moved here
from app.models import Product, ProductImage
from werkzeug.utils import secure_filename
def seed_database():
    with app.app_context():
        # Clear existing data to prevent duplicates and orphaned images
        ProductImage.query.delete()
        Product.query.delete()
        db.session.commit()
        print("Database cleared of default items. Ready for user listings.")

if __name__ == "__main__":
    seed_database()