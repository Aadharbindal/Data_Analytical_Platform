import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import DATA_DIR
from app.services.storage import s3_manager
from app.core.database import get_db_connection

def migrate_local_to_s3():
    print(f"Checking {DATA_DIR} for datasets to migrate...")
    if not os.path.exists(DATA_DIR):
        print("Data directory not found. Nothing to migrate.")
        return

    if not s3_manager.enabled:
        print("S3 Manager is not enabled! Please check your AWS/Supabase credentials in .env")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We want to get all valid datasets from the database to ensure we're migrating the right files
    cursor.execute("SELECT filepath FROM datasets WHERE filepath IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No datasets found in database.")
        return

    migrated_count = 0
    failed_count = 0

    for row in rows:
        filename = row[0]
        local_path = os.path.join(DATA_DIR, filename)
        
        if os.path.exists(local_path):
            print(f"Uploading {filename} to S3...")
            with open(local_path, "rb") as f:
                file_content = f.read()
                
            success = s3_manager.upload_file(file_content, filename)
            if success:
                print(f"Successfully migrated {filename}.")
                migrated_count += 1
            else:
                print(f"Failed to migrate {filename}.")
                failed_count += 1
        else:
            print(f"File {filename} is referenced in DB but not found locally.")

    print("\n--- Migration Summary ---")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Failed migrations: {failed_count}")

if __name__ == "__main__":
    migrate_local_to_s3()
