import pandas as pd
from typing import List, Dict, Any

from app.services.quality.completeness_engine import CompletenessEngine
from app.services.quality.consistency_engine import ConsistencyEngine
from app.services.quality.validity_engine import ValidityEngine
from app.services.quality.uniqueness_engine import UniquenessEngine
from app.services.quality.business_rule_engine import BusinessRuleEngine

class QualityOrchestrator:
    """Orchestrates all independent quality dimensions."""
    
    @staticmethod
    def evaluate_dataset(file_path: str, file_type: str, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        
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
            
        results = {
            "completeness": CompletenessEngine.evaluate(df, schema_metadata),
            "consistency": ConsistencyEngine.evaluate(df, schema_metadata),
            "validity": ValidityEngine.evaluate(df, schema_metadata),
            "uniqueness": UniquenessEngine.evaluate(df, schema_metadata),
            "business_rules": BusinessRuleEngine.evaluate(df, schema_metadata)
        }
        
        return results
