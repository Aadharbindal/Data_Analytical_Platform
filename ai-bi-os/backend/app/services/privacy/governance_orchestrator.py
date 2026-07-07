import polars as pl
from typing import List, Dict, Any

from app.services.privacy.pii_scanner import PIIScanner
from app.services.privacy.classification_engine import ClassificationEngine
from app.services.privacy.compliance_engine import ComplianceEngine
from app.services.privacy.risk_engine import RiskEngine

class GovernanceOrchestrator:
    """Coordinates the privacy, PII, and governance scanning."""
    
    @staticmethod
    def evaluate_dataset(file_path: str, file_type: str, schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        if file_type == 'csv':
            df = pl.read_csv(file_path, ignore_errors=True)
        elif file_type == 'parquet':
            df = pl.read_parquet(file_path)
        else:
            import pandas as pd
            if file_type == 'json':
                df = pl.from_pandas(pd.read_json(file_path, lines=True))
            else:
                df = pl.from_pandas(pd.read_excel(file_path))
                
        # 1. Scan for PII
        detections = PIIScanner.scan(df, schema_metadata)
        
        # 2. Classify
        classification = ClassificationEngine.classify(detections)
        
        # 3. Compliance
        compliance = ComplianceEngine.evaluate(detections)
        
        # 4. Risk
        risk = RiskEngine.calculate_scores(classification, compliance)
        
        return {
            "detections": detections,
            "classification": classification,
            "compliance": compliance,
            "risk": risk
        }
