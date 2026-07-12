import sys
import os
import io
import pandas as pd
import numpy as np

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_generator import generate_pdf_report

def main():
    # Synthetic dataset
    dates = pd.date_range(start='2025-01-01', periods=12, freq='M')
    data = {
        'date': dates,
        'revenue': np.random.randint(10000, 50000, size=12),
        'expenses': np.random.randint(5000, 20000, size=12),
        'segment': ['Retail', 'Wholesale', 'Online', 'Retail', 'Online', 'Wholesale'] * 2
    }
    df = pd.DataFrame(data)
    
    dataset_info = {
        'id': 'test_123',
        'name': 'Synthetic Test Data',
        'quality_score': 92.5,
        'quality_breakdown': '{"completeness": 95, "uniqueness": 100, "type_consistency": 90, "validity": 85}'
    }
    
    print("Generating PDF...")
    try:
        pdf_buffer = generate_pdf_report(dataset_info, df)
        output_path = "test_redesign_output.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_buffer.read())
        print(f"PDF generated successfully at {output_path}")
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
