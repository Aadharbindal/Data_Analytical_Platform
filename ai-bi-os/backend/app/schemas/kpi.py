from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class KPIVersionSchema(BaseModel):
    version_number: int
    author: Optional[str]
    status: str
    formula_expression: str
    dependencies: Optional[List[str]]
    activation_date: datetime
    
    class Config:
        from_attributes = True

class KPIDefinitionSchema(BaseModel):
    id: str
    workspace_id: str
    name: str
    category: str
    description: Optional[str]
    is_custom: bool
    
    class Config:
        from_attributes = True

class KPICalculationSchema(BaseModel):
    id: str
    definition_id: str
    dataset_version_id: str
    dimension: Optional[str]
    dimension_value: Optional[str]
    time_window: Optional[str]
    value: float
    previous_value: Optional[float]
    confidence_score: Optional[float]
    calculated_at: datetime
    
    class Config:
        from_attributes = True

class KPICreateRequest(BaseModel):
    workspace_id: str
    name: str
    category: str
    description: Optional[str]
    formula: str
    author: str
    dependencies: Optional[List[str]] = []

class KPICalculateRequest(BaseModel):
    workspace_id: str
    dataset_version_id: str
    definition_id: str
    dimension: Optional[str] = None
