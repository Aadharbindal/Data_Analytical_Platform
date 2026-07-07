import pandas as pd
from typing import Dict, Any, List

from app.services.profiling.numeric_profiler import NumericProfiler
from app.services.profiling.string_profiler import StringProfiler
from app.services.profiling.date_profiler import DateProfiler
from app.services.profiling.category_profiler import CategoryProfiler
from app.services.profiling.outlier_detector import OutlierDetector
from app.services.profiling.distribution_analyzer import DistributionAnalyzer

class DatasetProfiler:
    """
    Orchestrates the massive data profiling workload.
    """
    @staticmethod
    def analyze_dataset(file_path: str, file_type: str, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Loads the dataset and computes deep statistical profiles based on the detected schema.
        """
        # Load dataset
        if file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_type == 'json':
            df = pd.read_json(file_path, lines=True)
        elif file_type == 'parquet':
            df = pd.read_parquet(file_path)
        elif file_type in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        total_rows = len(df)
        total_cols = len(df.columns)
        memory_usage = df.memory_usage(deep=True).sum()
        
        # Global Metrics
        global_nulls = df.isnull().sum().sum()
        total_cells = total_rows * total_cols
        sparsity = float(global_nulls / total_cells) if total_cells > 0 else 0.0
        dataset_density = 1.0 - sparsity
        
        columns_profile = []
        
        for col_schema in schema_metadata:
            col_name = col_schema["original_header"]
            if col_name not in df.columns:
                continue
                
            series = df[col_name]
            
            # Base Column Metrics
            null_count = int(series.isnull().sum())
            non_null_count = total_rows - null_count
            null_percentage = float(null_count / total_rows) if total_rows > 0 else 0.0
            
            unique_count = int(series.nunique(dropna=True))
            duplicate_count = non_null_count - unique_count
            duplicate_percentage = float(duplicate_count / non_null_count) if non_null_count > 0 else 0.0
            distinct_ratio = float(unique_count / non_null_count) if non_null_count > 0 else 0.0
            
            # Entropy
            import numpy as np
            value_counts = series.value_counts(normalize=True).values
            entropy = float(-np.sum(value_counts * np.log2(value_counts))) if len(value_counts) > 0 else 0.0
            
            profile_payload = {
                "schema_column_id": col_schema["id"],
                "column_name": col_name,
                "null_count": null_count,
                "non_null_count": non_null_count,
                "null_percentage": null_percentage,
                "unique_count": unique_count,
                "duplicate_count": duplicate_count,
                "duplicate_percentage": duplicate_percentage,
                "distinct_ratio": distinct_ratio,
                "entropy_score": entropy,
                "sub_profiles": {}
            }
            
            classification = col_schema.get("classification")
            semantic_type = col_schema.get("inferred_semantic_type")
            
            # Conditionally run deep profilers based on schema intelligence
            if classification == "Measure" or semantic_type in ["Integer", "Float"]:
                profile_payload["sub_profiles"]["numeric"] = NumericProfiler.profile(series)
                profile_payload["sub_profiles"]["outlier"] = OutlierDetector.detect(series)
                profile_payload["sub_profiles"]["distribution"] = DistributionAnalyzer.profile(series)
                
            elif classification == "Dimension" or semantic_type == "Categorical":
                profile_payload["sub_profiles"]["category"] = CategoryProfiler.profile(series)
                profile_payload["sub_profiles"]["string"] = StringProfiler.profile(series)
                
            elif classification == "Timestamp" or semantic_type in ["Date", "Datetime"]:
                profile_payload["sub_profiles"]["date"] = DateProfiler.profile(series)
                
            elif semantic_type in ["Text", "Email", "URL"]:
                profile_payload["sub_profiles"]["string"] = StringProfiler.profile(series)
                
            columns_profile.append(profile_payload)
            
        return {
            "global": {
                "number_of_rows": total_rows,
                "number_of_columns": total_cols,
                "memory_usage_bytes": int(memory_usage),
                "sparsity": sparsity,
                "dataset_density": dataset_density
            },
            "columns": columns_profile
        }
