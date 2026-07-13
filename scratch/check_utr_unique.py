import pandas as pd
import sys
import os

sys.path.append(r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend')

data_dir = r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend\data'
for filename in os.listdir(data_dir):
    if filename.endswith('.csv') and 'upi_bank_statement' in filename:
        filepath = os.path.join(data_dir, filename)
        df = pd.read_csv(filepath)
        print(f"File: {filename}")
        print(f"  Total rows: {len(df)}")
        if 'UTR' in df.columns:
            print(f"  Unique UTR: {df['UTR'].nunique()}")
        if 'UPI_ID' in df.columns:
            print(f"  Unique UPI_ID: {df['UPI_ID'].nunique()}")
