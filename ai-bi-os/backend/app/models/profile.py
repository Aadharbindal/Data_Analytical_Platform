from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    dataset_name = Column(String, nullable=True)
    number_of_rows = Column(Integer, default=0)
    number_of_columns = Column(Integer, default=0)
    memory_usage_bytes = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    dataset_density = Column(Float, default=0.0)
    sparsity = Column(Float, default=0.0)
    
    dataset_completeness_score = Column(Float, default=0.0)
    consistency_indicator = Column(Float, default=0.0)
    readiness_score = Column(Float, default=0.0)
    
    # Relationships
    version = relationship("DatasetVersion")
    columns = relationship("ColumnProfile", back_populates="profile", cascade="all, delete-orphan")

class ColumnProfile(Base):
    __tablename__ = "column_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_profile_id = Column(String, ForeignKey("dataset_profiles.id"))
    schema_column_id = Column(String, ForeignKey("schema_columns.id"))
    
    column_name = Column(String, nullable=False)
    null_count = Column(Integer, default=0)
    null_percentage = Column(Float, default=0.0)
    non_null_count = Column(Integer, default=0)
    unique_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    duplicate_percentage = Column(Float, default=0.0)
    distinct_ratio = Column(Float, default=0.0)
    entropy_score = Column(Float, default=0.0)
    
    profile = relationship("DatasetProfile", back_populates="columns")
    schema_column = relationship("SchemaColumn")
    
    numeric_profile = relationship("NumericProfile", back_populates="column", uselist=False, cascade="all, delete-orphan")
    string_profile = relationship("StringProfile", back_populates="column", uselist=False, cascade="all, delete-orphan")
    date_profile = relationship("DateProfile", back_populates="column", uselist=False, cascade="all, delete-orphan")
    category_profile = relationship("CategoryProfile", back_populates="column", uselist=False, cascade="all, delete-orphan")
    outlier_profile = relationship("OutlierProfile", back_populates="column", uselist=False, cascade="all, delete-orphan")
    distribution_profile = relationship("ColDistributionProfile", back_populates="column", uselist=False, cascade="all, delete-orphan")

class NumericProfile(Base):
    __tablename__ = "numeric_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    column_profile_id = Column(String, ForeignKey("column_profiles.id"), unique=True)
    
    minimum = Column(Float, nullable=True)
    maximum = Column(Float, nullable=True)
    mean = Column(Float, nullable=True)
    median = Column(Float, nullable=True)
    mode = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
    range_val = Column(Float, nullable=True)
    sum_val = Column(Float, nullable=True)
    
    q1 = Column(Float, nullable=True)
    q3 = Column(Float, nullable=True)
    iqr = Column(Float, nullable=True)
    percentiles = Column(JSON, nullable=True) # Dict of 5,10,25,50,75,90,95,99
    
    cv = Column(Float, nullable=True) # Coefficient of variation
    skewness = Column(Float, nullable=True)
    kurtosis = Column(Float, nullable=True)
    
    zero_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    
    column = relationship("ColumnProfile", back_populates="numeric_profile")

class StringProfile(Base):
    __tablename__ = "string_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    column_profile_id = Column(String, ForeignKey("column_profiles.id"), unique=True)
    
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    avg_length = Column(Float, nullable=True)
    
    uppercase_ratio = Column(Float, nullable=True)
    lowercase_ratio = Column(Float, nullable=True)
    whitespace_count = Column(Integer, default=0)
    empty_string_count = Column(Integer, default=0)
    special_char_count = Column(Integer, default=0)
    
    column = relationship("ColumnProfile", back_populates="string_profile")

class DateProfile(Base):
    __tablename__ = "date_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    column_profile_id = Column(String, ForeignKey("column_profiles.id"), unique=True)
    
    earliest_date = Column(DateTime, nullable=True)
    latest_date = Column(DateTime, nullable=True)
    date_range_days = Column(Integer, nullable=True)
    weekend_ratio = Column(Float, nullable=True)
    
    monthly_distribution = Column(JSON, nullable=True)
    year_distribution = Column(JSON, nullable=True)
    
    column = relationship("ColumnProfile", back_populates="date_profile")

class CategoryProfile(Base):
    __tablename__ = "category_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    column_profile_id = Column(String, ForeignKey("column_profiles.id"), unique=True)
    
    top_categories = Column(JSON, nullable=True)
    bottom_categories = Column(JSON, nullable=True)
    category_balance_score = Column(Float, nullable=True)
    
    column = relationship("ColumnProfile", back_populates="category_profile")

class OutlierProfile(Base):
    __tablename__ = "outlier_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    column_profile_id = Column(String, ForeignKey("column_profiles.id"), unique=True)
    
    iqr_outlier_count = Column(Integer, default=0)
    zscore_outlier_count = Column(Integer, default=0)
    outlier_percentage = Column(Float, default=0.0)
    
    column = relationship("ColumnProfile", back_populates="outlier_profile")

class ColDistributionProfile(Base):
    __tablename__ = "col_distribution_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    column_profile_id = Column(String, ForeignKey("column_profiles.id"), unique=True)
    
    distribution_type = Column(String, default="Unknown") # Normal, Uniform, Exponential, etc.
    confidence_score = Column(Float, default=0.0)
    histogram_bins = Column(JSON, nullable=True) # Metadata for UI
    
    column = relationship("ColumnProfile", back_populates="distribution_profile")
