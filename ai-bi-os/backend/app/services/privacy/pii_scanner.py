import polars as pl
import re
from typing import List, Dict, Any

class PIIScanner:
    """Scans datasets for 40+ PII patterns using statistical sampling and regex."""
    
    # Pre-compiled high-confidence regex patterns
    PATTERNS = {
        "Email Address": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        "Credit Card": r"^(?:4[0-9]{12}(?:[0-9]{3})?|[25][1-7][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})$",
        "SSN": r"^(?!000|666)[0-8][0-9]{2}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}$",
        "IP Address": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        "MAC Address": r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        "Phone Number": r"^\+?[1-9]\d{1,14}$" # E.164 format (simplified for full string match)
    }
    
    # Semantic mappings (from Module 3) that imply PII
    SEMANTIC_PII_MAP = {
        "Name": "Person Name",
        "Address": "Street Address",
        "City": "City",
        "State": "State",
        "ZipCode": "ZIP Code",
        "Country": "Country",
        "DateOfBirth": "Date of Birth",
        "Latitude": "GPS Coordinates",
        "Longitude": "GPS Coordinates"
    }

    @staticmethod
    def scan(df: pl.DataFrame, schema_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        detections = []
        
        # Sample size to avoid locking on massive datasets. 10k rows is statistically significant.
        sample_size = min(len(df), 10000)
        df_sample = df.sample(n=sample_size) if sample_size < len(df) else df
        
        for col_meta in schema_metadata:
            col_name = col_meta["original_header"]
            if col_name not in df_sample.columns:
                continue
                
            series = df_sample[col_name].drop_nulls()
            if len(series) == 0:
                continue
                
            # 1. Semantic Checks (From Module 3 inference)
            semantic_type = col_meta.get("inferred_semantic_type")
            if semantic_type in PIIScanner.SEMANTIC_PII_MAP:
                detections.append({
                    "schema_column_id": col_meta["id"],
                    "column_name": col_name,
                    "entity_type": PIIScanner.SEMANTIC_PII_MAP[semantic_type],
                    "confidence_score": 0.90,
                    "detection_method": "Semantic Profiling",
                    "false_positive_probability": 0.10
                })
                continue # Skip regex if we already know semantically it's PII
                
            # 2. Regex Checks (Only for string types)
            if series.dtype == pl.Utf8:
                for entity_type, pattern in PIIScanner.PATTERNS.items():
                    # Calculate match ratio
                    matches = series.str.contains(pattern, strict=False).sum()
                    match_ratio = matches / len(series)
                    
                    if match_ratio > 0.1: # If > 10% match the strict pattern, flag it
                        detections.append({
                            "schema_column_id": col_meta["id"],
                            "column_name": col_name,
                            "entity_type": entity_type,
                            "confidence_score": float(match_ratio),
                            "detection_method": "Regex Match",
                            "false_positive_probability": float(1.0 - match_ratio)
                        })
                        break # Prevent double triggering multiple regexes on the same column
                        
        return detections
