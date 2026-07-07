import pandas as pd
import re
from typing import List, Dict, Any

from app.services.schema.type_inference import TypeInferenceService
from app.services.schema.semantic_detection import SemanticDetectionService
from app.services.schema.key_detection import KeyDetectionService

class SchemaDiscoveryService:
    """
    Orchestrates the entire schema extraction and intelligence pipeline for a dataset.
    """
    
    @staticmethod
    def _normalize_header(header: str) -> str:
        # Lowercase, replace spaces/special chars with underscore, strip leading/trailing
        normalized = re.sub(r'[^a-zA-Z0-9]+', '_', str(header).lower()).strip('_')
        # Reserved keywords check could go here if generating SQL
        return normalized

    @classmethod
    def analyze_dataset(cls, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Reads the file, runs it through the intelligence engines, and returns a list of column metadata.
        """
        # 1. Load data sample (up to 100k rows for deep inference)
        if file_type == 'csv':
            df = pd.read_csv(file_path, nrows=100000)
        elif file_type == 'json':
            # handle JSON appropriately, assume lines for large files or flat array
            df = pd.read_json(file_path, lines=True, chunksize=100000)
            df = next(iter(df)) if df else pd.DataFrame()
        elif file_type == 'parquet':
            # Parquet reads are fast, but we can sample
            df = pd.read_parquet(file_path)
            if len(df) > 100000:
                df = df.sample(100000)
        elif file_type in ['xlsx', 'xls']:
            df = pd.read_excel(file_path, nrows=100000)
        else:
            raise ValueError(f"Unsupported file type for schema analysis: {file_type}")
            
        schema_metadata = []
        
        # 2. Iterate through columns and build intelligence
        for position, original_header in enumerate(df.columns):
            series = df[original_header]
            
            normalized_header = cls._normalize_header(original_header)
            detected_data_type = str(series.dtype)
            
            # Run Intelligence Engines
            semantic_type = TypeInferenceService.infer_semantic_type(series)
            business_meaning = SemanticDetectionService.infer_business_meaning(original_header)
            classification = SemanticDetectionService.classify_column(original_header, semantic_type, business_meaning)
            keys = KeyDetectionService.detect_keys(series, original_header)
            
            is_nullable = bool(series.isnull().any())
            
            col_meta = {
                "position": position,
                "original_header": str(original_header),
                "normalized_header": normalized_header,
                "detected_data_type": detected_data_type,
                "inferred_semantic_type": semantic_type,
                "business_meaning": business_meaning,
                "classification": classification,
                "is_nullable": is_nullable,
                "is_unique": keys["is_unique"],
                "is_primary_key_candidate": keys["is_pk_candidate"],
                "is_foreign_key_candidate": keys["is_fk_candidate"]
            }
            schema_metadata.append(col_meta)
            
        return schema_metadata
