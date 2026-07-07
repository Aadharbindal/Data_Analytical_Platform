import pandas as pd
from typing import Dict, Any, List

class SemanticSchemaGenerator:
    """Infers data types and business semantic meaning from datasets."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def infer_types(self) -> Dict[str, str]:
        """Infers basic data types (string, integer, float, date)."""
        types = {}
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            if "int" in dtype:
                types[col] = "integer"
            elif "float" in dtype:
                types[col] = "numeric"
            elif "datetime" in dtype:
                types[col] = "date"
            else:
                types[col] = "categorical"
        return types

    def infer_semantics(self) -> Dict[str, str]:
        """Infers business semantics (e.g., Revenue, Region, Customer ID)."""
        semantics = {}
        for col in self.df.columns:
            col_lower = col.lower()
            if "rev" in col_lower or "sales" in col_lower or "amount" in col_lower:
                semantics[col] = "currency/revenue"
            elif "id" in col_lower:
                semantics[col] = "identifier"
            elif "date" in col_lower or "time" in col_lower:
                semantics[col] = "temporal"
            elif "region" in col_lower or "country" in col_lower or "city" in col_lower:
                semantics[col] = "geospatial"
            else:
                semantics[col] = "unknown"
        return semantics

    def generate_schema(self) -> Dict[str, Any]:
        """Generates the full semantic schema for the dataset."""
        return {
            "columns": list(self.df.columns),
            "inferred_types": self.infer_types(),
            "business_semantics": self.infer_semantics()
        }
