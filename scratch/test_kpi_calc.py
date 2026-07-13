import pandas as pd
import sys
import os

sys.path.append(r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend')

from app.services.semantic_classification import fallback_classify
from app.services.stats_service import compute_kpis

# Let's find the files in ai-bi-os/backend/data
data_dir = r'c:\Users\user\Documents\Data_Analytics\ai-bi-os\backend\data'
files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]

for f in files:
    filename = os.path.basename(f)
    print(f"\nFile: {filename}")
    try:
        df = pd.read_csv(f)
        print(f"Shape: {df.shape}")
        domain, sem_dict = fallback_classify(df, filename)
        print("Classified Domain:", domain)
        print("Business Terminology:", sem_dict.get("business_terminology", {}))
        kpis = compute_kpis(df, sem_dict)
        print("KPIs:")
        for kpi in kpis.get("kpis", []):
            print(f"  - {kpi['name']} ({kpi['column']}): {kpi['value']} (type: {kpi.get('type')})")
    except Exception as e:
        print("Error processing file:", str(e))

