import os
import psycopg2
from dotenv import load_dotenv

print("--- Database Connection Test ---")

# Ensure we are loading the .env file from the correct directory
project_root = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(project_root, '.env')

if not os.path.exists(dotenv_path):
    print(f"ERROR: .env file not found at {dotenv_path}")
else:
    print("Attempting to load .env file...")
    load_dotenv(dotenv_path=dotenv_path)
    print(".env file loaded.")

    db_url = os.environ.get('DATABASE_URL')

    if not db_url:
        print("\nERROR: DATABASE_URL not found in environment variables.")
        print("Please ensure it is correctly set in your .env file.")
    else:
        print("\nFound DATABASE_URL. Attempting to connect...")
        try:
            conn = psycopg2.connect(db_url)
            print("\n******************************************")
            print(">>> SUCCESS: Connection established! <<<")
            print("******************************************")
            conn.close()
            print("Connection closed.")
        except Exception as e:
            print("\n******************************************")
            print(">>> FAILURE: Could not connect. <<<")
            print("******************************************")
            print(f"\nThe specific error was:\n{e}")

print("\n--- Test Complete ---")
