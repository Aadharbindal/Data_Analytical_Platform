import sys
import os
import io
import pandas as pd
import numpy as np

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_generator import generate_pdf_report

def main():
    # Synthetic dataset with no date
    data = {
        'Amount': np.random.randint(10000, 50000, size=12),
        'Branch': ['Retail', 'Wholesale', 'Online', 'Retail', 'Online', 'Wholesale'] * 2
    }
    df = pd.DataFrame(data)
    
    dataset_info = {
        'id': 'test_no_date',
        'name': 'Synthetic Test Data (No Date)',
        'quality_score': 92.5,
        'quality_breakdown': '{"completeness": 95, "uniqueness": 100, "type_consistency": 90, "validity": 85}'
    }
    
    print("Generating PDF without date...")
    try:
        pdf_buffer = generate_pdf_report(dataset_info, df)
        output_path = "test_redesign_nodate.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_buffer.read())
        print(f"PDF generated successfully at {output_path}")
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
