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
from app.models import PriceHistory, Product, ProductImage, User, CartItem, Message, Order  # noqa
def seed_database():
    app = create_app()
    with app.app_context():
        print("Connecting to services...")
        
        # BONUS: Clear the Supabase storage bucket to remove orphaned files
        try:
            supabase_client = app.config['SUPABASE_CLIENT']
            bucket_name = app.config['SUPABASE_BUCKET']
            print(f"Listing files in bucket '{bucket_name}'...")
            all_files = supabase_client.storage.from_(bucket_name).list()
            if all_files:
                file_paths = [file['name'] for file in all_files]
                print(f"Deleting {len(file_paths)} files from storage...")
                supabase_client.storage.from_(bucket_name).remove(file_paths)
            else:
                print("Storage bucket is already empty.")
        except Exception as e:
            print(f"Warning: Could not clear Supabase bucket. Error: {e}")

        # Clear existing data to prevent duplicates and orphaned images
        print("Clearing database tables...")
        CartItem.query.delete()
        Message.query.delete()
        Order.query.delete()
        ProductImage.query.delete()
        PriceHistory.query.delete()
        Product.query.delete()
        User.query.delete()
        db.session.commit()
        print("Database and storage are now clean.")

if __name__ == "__main__":
    seed_database()