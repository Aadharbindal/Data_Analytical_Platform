import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.data_processing import get_active_dataset, get_dataframe
from app.services.pdf_generator import generate_pdf_report

user_id = "default_user" # Assuming default_user is used if no auth, let's just query sqlite directly

import sqlite3
from app.core.config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT user_id FROM datasets LIMIT 1")
row = cursor.fetchone()
conn.close()

if row:
    user_id = row['user_id']
    print(f"Using user_id: {user_id}")
    dataset_info = get_active_dataset(user_id)
    if dataset_info:
        df = get_dataframe(dataset_info["id"], user_id)
        if df is not None:
            print("Dataset found, generating PDF...")
            try:
                pdf_buffer = generate_pdf_report(dataset_info, df)
                print("PDF generated successfully! Size:", len(pdf_buffer.getvalue()))
            except Exception as e:
                import traceback
                traceback.print_exc()
        else:
            print("DF is None")
    else:
        print("No active dataset")
else:
    print("No users found in db")
