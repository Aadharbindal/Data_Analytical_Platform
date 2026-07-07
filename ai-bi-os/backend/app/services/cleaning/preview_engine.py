import polars as pl
from typing import List, Dict, Any
import json

from app.services.cleaning.transformation_engine import TransformationEngine

class PreviewEngine:
    """Provides a fast JSON before/after diff for UI consumption."""
    
    @staticmethod
    def generate_preview(file_path: str, file_type: str, steps: List[Dict[str, Any]], sample_size: int = 100) -> Dict[str, Any]:
        
        # Load sample using Polars lazy frames where possible, or just head
        if file_type == 'csv':
            df_before = pl.read_csv(file_path, n_rows=sample_size)
        elif file_type == 'parquet':
            # read_parquet does not have n_rows directly, but we can slice
            df_before = pl.read_parquet(file_path).head(sample_size)
        elif file_type == 'json':
            # Pandas is often safer for nested JSON, but let's try polars first
            try:
                df_before = pl.read_ndjson(file_path).head(sample_size)
            except:
                import pandas as pd
                df_before = pl.from_pandas(pd.read_json(file_path, lines=True).head(sample_size))
        else:
            # Excel fallback via pandas
            import pandas as pd
            df_before = pl.from_pandas(pd.read_excel(file_path).head(sample_size))
            
        before_records = df_before.to_dicts()
        
        # Apply transformation
        df_after = TransformationEngine.execute_pipeline(df_before.clone(), steps)
        after_records = df_after.to_dicts()
        
        return {
            "before_sample": before_records,
            "after_sample": after_records,
            "affected_columns": list(set(df_before.columns) ^ set(df_after.columns)) + [s.get("target_column") for s in steps if s.get("target_column")],
            "steps_simulated": len(steps)
        }
