from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class NumericProfileResponse(BaseModel):
    minimum: Optional[float]
    maximum: Optional[float]
    mean: Optional[float]
    median: Optional[float]
    mode: Optional[float]
    std_dev: Optional[float]
    variance: Optional[float]
    range_val: Optional[float]
    sum_val: Optional[float]
    q1: Optional[float]
    q3: Optional[float]
    iqr: Optional[float]
    percentiles: Optional[Dict[str, float]]
    cv: Optional[float]
    skewness: Optional[float]
    kurtosis: Optional[float]
    zero_count: int
    negative_count: int
    positive_count: int
    
    class Config:
        from_attributes = True

class StringProfileResponse(BaseModel):
    min_length: Optional[int]
    max_length: Optional[int]
    avg_length: Optional[float]
    uppercase_ratio: Optional[float]
    lowercase_ratio: Optional[float]
    whitespace_count: int
    empty_string_count: int
    special_char_count: int
    
    class Config:
        from_attributes = True

class DateProfileResponse(BaseModel):
    earliest_date: Optional[datetime]
    latest_date: Optional[datetime]
    date_range_days: Optional[int]
    weekend_ratio: Optional[float]
    monthly_distribution: Optional[Dict[str, float]]
    year_distribution: Optional[Dict[str, float]]
    
    class Config:
        from_attributes = True

class CategoryProfileResponse(BaseModel):
    top_categories: Optional[Dict[str, float]]
    bottom_categories: Optional[Dict[str, float]]
    category_balance_score: Optional[float]
    
    class Config:
        from_attributes = True

class OutlierProfileResponse(BaseModel):
    iqr_outlier_count: int
    zscore_outlier_count: int
    outlier_percentage: float
    
    class Config:
        from_attributes = True

class DistributionProfileResponse(BaseModel):
    distribution_type: str
    confidence_score: float
    histogram_bins: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class ColumnProfileResponse(BaseModel):
    id: str
    schema_column_id: str
    column_name: str
    null_count: int
    null_percentage: float
    non_null_count: int
    unique_count: int
    duplicate_count: int
    duplicate_percentage: float
    distinct_ratio: float
    entropy_score: float
    
    numeric_profile: Optional[NumericProfileResponse] = None
    string_profile: Optional[StringProfileResponse] = None
    date_profile: Optional[DateProfileResponse] = None
    category_profile: Optional[CategoryProfileResponse] = None
    outlier_profile: Optional[OutlierProfileResponse] = None
    distribution_profile: Optional[DistributionProfileResponse] = None

    class Config:
        from_attributes = True

class DatasetProfileResponse(BaseModel):
    id: str
    dataset_version_id: str
    created_at: datetime
    
    number_of_rows: int
    number_of_columns: int
    memory_usage_bytes: int
    sparsity: float
    dataset_density: float
    readiness_score: float
    
    columns: List[ColumnProfileResponse] = []
    
    class Config:
        from_attributes = True

class DatasetProfileSummaryResponse(BaseModel):
    id: str
    number_of_rows: int
    number_of_columns: int
    memory_usage_bytes: int
    dataset_density: float
    readiness_score: float
    
    class Config:
        from_attributes = True
