import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.services.pdf_generator import generate_pdf_report
import pandas as pd
import numpy as np

df = pd.read_csv('backend/data/0cddbdbc-ba08-4b45-a582-c792e8f72b9e_electronics_sales_BIG.csv')
dataset_info = {'id': '0cddbdbc-ba08-4b45-a582-c792e8f72b9e', 'name': 'Electronics Sales', 'quality_score': 95, 'quality_breakdown': '{"completeness": 100, "uniqueness": 95, "type_consistency": 90, "validity": 100}'}

try:
    buffer = generate_pdf_report(dataset_info, df)
    with open('test_output.pdf', 'wb') as f:
        f.write(buffer.read())
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
