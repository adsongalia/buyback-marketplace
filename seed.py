import os
import uuid
from dotenv import load_dotenv
# Explicitly load .env for standalone script execution
project_root = os.path.abspath(os.path.dirname(__file__)) # Corrected path
dotenv_path = os.path.join(project_root, '.env')
if not os.path.exists(dotenv_path):
    print("ERROR: .env file not found. Please create one in the project root before seeding.")
    exit(1)

load_dotenv(dotenv_path=dotenv_path)
if not os.environ.get('DATABASE_URL'):
    print("ERROR: DATABASE_URL not found in .env file. Please add it before seeding.")
    exit(1)

from app import create_app, db  # noqa
from app.models import PriceHistory, Product, ProductImage, User  # noqa
def seed_database():
    app = create_app()
    with app.app_context():
        print("Connecting to database...")
        # Clear existing data to prevent duplicates and orphaned images
        print("Clearing existing data...")
        ProductImage.query.delete()
        PriceHistory.query.delete()
        Product.query.delete()
        User.query.delete()
        db.session.commit()
        print("Database cleared. It is now ready for users to populate.")

if __name__ == "__main__":
    seed_database()