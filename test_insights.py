import sys
import os
sys.path.append(os.path.abspath("ai-bi-os/backend"))

from app.services.insight_candidates import generate_candidates
import pandas as pd

# Dummy data
data = {
    "category": ["A", "A", "B", "B", "C"],
    "revenue": [100, 150, 50, 10, 5],
    "status": ["ok", "fail", "ok", "fail", "cancel"],
    "date": ["2023-01-01", "2023-01-01", "2023-02-01", "2023-02-01", "2023-02-01"]
}
df = pd.DataFrame(data)

sem_dict = {
    "business_terminology": {
        "primary_metric": "revenue",
        "status_col": "status",
        "status_unhealthy_regex": "fail|cancel"
    },
    "semantic_dictionary": {
        "categorical_fields": ["category"],
        "date_columns": ["date"]
    }
}

candidates = generate_candidates(df, sem_dict)
print("Generated Candidates:")
for c in candidates:
    print(c)
