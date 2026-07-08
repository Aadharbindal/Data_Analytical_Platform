from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RunStatisticsRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    population_size: int
    metrics: List[Dict[str, Any]] # [{'name': 'col1', 'type': 'NUMERIC', 'stats': {...}}]

class StatisticsRunResponse(BaseModel):
    run_id: str
    status: str
    execution_time_ms: float
    total_tests_run: int
    significant_results_found: int

class HypothesisTestResponse(BaseModel):
    test_name: str
    target_metric: str
    test_statistic: float
    p_value: float
    degrees_of_freedom: Optional[float]
    reject_null_hypothesis: bool

class ConfidenceIntervalResponse(BaseModel):
    metric_name: str
    confidence_level: float
    mean_estimate: float
    margin_of_error: float
    lower_bound: float
    upper_bound: float

class DistributionProfileResponse(BaseModel):
    column_name: str
    best_fit_distribution: str
    goodness_of_fit_test: str
    p_value: float
    distribution_parameters: Optional[Dict[str, Any]]

class InferenceResultResponse(BaseModel):
    business_metric: str
    statistical_method: str
    significance_level: str
    confidence_description: str
    risk_level: str
    supporting_statistics: Optional[Dict[str, Any]]
