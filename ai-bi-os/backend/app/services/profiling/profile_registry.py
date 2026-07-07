from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.models.profile import (
    DatasetProfile, ColumnProfile, NumericProfile, StringProfile, 
    DateProfile, CategoryProfile, OutlierProfile, ColDistributionProfile
)
from app.models.dataset import DatasetVersion

class ProfileRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def save_profile(self, dataset_version_id: str, profile_data: Dict[str, Any]) -> DatasetProfile:
        # Check and delete existing profile for this version
        existing = self.db.query(DatasetProfile).filter(DatasetProfile.dataset_version_id == dataset_version_id).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()
            
        global_data = profile_data["global"]
        
        # Calculate completeness
        # Assume high density = high completeness
        readiness_score = global_data["dataset_density"] * 100.0
        
        profile = DatasetProfile(
            dataset_version_id=dataset_version_id,
            number_of_rows=global_data["number_of_rows"],
            number_of_columns=global_data["number_of_columns"],
            memory_usage_bytes=global_data["memory_usage_bytes"],
            sparsity=global_data["sparsity"],
            dataset_density=global_data["dataset_density"],
            readiness_score=readiness_score
        )
        self.db.add(profile)
        self.db.flush()
        
        for col_data in profile_data["columns"]:
            col_profile = ColumnProfile(
                dataset_profile_id=profile.id,
                schema_column_id=col_data["schema_column_id"],
                column_name=col_data["column_name"],
                null_count=col_data["null_count"],
                null_percentage=col_data["null_percentage"],
                non_null_count=col_data["non_null_count"],
                unique_count=col_data["unique_count"],
                duplicate_count=col_data["duplicate_count"],
                duplicate_percentage=col_data["duplicate_percentage"],
                distinct_ratio=col_data["distinct_ratio"],
                entropy_score=col_data["entropy_score"]
            )
            self.db.add(col_profile)
            self.db.flush()
            
            sub = col_data.get("sub_profiles", {})
            
            if "numeric" in sub and sub["numeric"]:
                num_p = NumericProfile(column_profile_id=col_profile.id, **sub["numeric"])
                self.db.add(num_p)
                
            if "string" in sub and sub["string"]:
                str_p = StringProfile(column_profile_id=col_profile.id, **sub["string"])
                self.db.add(str_p)
                
            if "date" in sub and sub["date"]:
                # Cast string dates back to datetime obj if present
                import dateutil.parser
                dp = sub["date"]
                if dp.get("earliest_date"): dp["earliest_date"] = dateutil.parser.isoparse(dp["earliest_date"])
                if dp.get("latest_date"): dp["latest_date"] = dateutil.parser.isoparse(dp["latest_date"])
                date_p = DateProfile(column_profile_id=col_profile.id, **dp)
                self.db.add(date_p)
                
            if "category" in sub and sub["category"]:
                cat_p = CategoryProfile(column_profile_id=col_profile.id, **sub["category"])
                self.db.add(cat_p)
                
            if "outlier" in sub and sub["outlier"]:
                out_p = OutlierProfile(column_profile_id=col_profile.id, **sub["outlier"])
                self.db.add(out_p)
                
            if "distribution" in sub and sub["distribution"]:
                dist_p = ColDistributionProfile(column_profile_id=col_profile.id, **sub["distribution"])
                self.db.add(dist_p)

        self.db.commit()
        return profile
        
    def get_profile_for_dataset(self, dataset_id: str) -> Optional[DatasetProfile]:
        # We fetch the profile for the LATEST active version
        latest_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.is_active == True
        ).first()
        
        if not latest_version:
            return None
            
        return self.db.query(DatasetProfile).filter(DatasetProfile.dataset_version_id == latest_version.id).first()
