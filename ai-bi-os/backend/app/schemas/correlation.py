from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RunCorrelationRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    columns_meta: List[Dict[str, str]] # [{'name': 'col1', 'type': 'NUMERIC'}]

class CorrelationRunResponse(BaseModel):
    run_id: str
    status: str
    execution_time_ms: float
    pairs_evaluated: int
    significant_relationships: int

class FeatureRelationshipResponse(BaseModel):
    source_metric: str
    target_metric: str
    relationship_type: str
    business_relevance: Optional[str]
    supporting_statistics: Optional[Dict[str, Any]]

class PairwiseCorrelationResponse(BaseModel):
    column_x: str
    column_y: str
    method_used: str
    coefficient: float
    p_value: float
    is_significant: bool
    strength_classification: str

class CorrelationMatrixResponse(BaseModel):
    matrix_type: str
    data: Dict[str, Any]
