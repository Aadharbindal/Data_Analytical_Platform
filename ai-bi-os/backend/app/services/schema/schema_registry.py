import hashlib
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.schema import DatasetSchema, SchemaColumn, SchemaFingerprint, SchemaQuality

class SchemaRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def generate_hashes(self, columns_metadata: List[Dict[str, Any]]) -> dict:
        # Schema Hash: Based on names and pure types
        schema_str = "|".join([f"{c['normalized_header']}:{c['detected_data_type']}" for c in columns_metadata])
        schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
        
        # Column Hash: Based on normalized names only
        col_str = "|".join([c['normalized_header'] for c in columns_metadata])
        column_hash = hashlib.sha256(col_str.encode()).hexdigest()
        
        # Structure Hash: Includes constraints and semantic types
        struct_str = "|".join([f"{c['normalized_header']}:{c['inferred_semantic_type']}:{c['is_nullable']}" for c in columns_metadata])
        structure_hash = hashlib.sha256(struct_str.encode()).hexdigest()
        
        # Dataset Signature: Combined
        dataset_signature = hashlib.md5(f"{schema_hash}-{structure_hash}".encode()).hexdigest()
        
        return {
            "schema_hash": schema_hash,
            "column_hash": column_hash,
            "structure_hash": structure_hash,
            "dataset_signature": dataset_signature
        }
        
    def calculate_quality(self, columns: List[Dict[str, Any]]) -> dict:
        total = len(columns)
        if total == 0:
            return {"completeness_score": 0.0, "naming_quality_score": 0.0, "consistency_score": 0.0, "normalization_score": 0.0, "relationship_score": 0.0, "overall_quality_score": 0.0}
            
        # Naming Quality: Does original match normalized well? Or are there lots of special chars?
        naming_matches = sum(1 for c in columns if c['original_header'].lower() == c['normalized_header'])
        naming_quality = naming_matches / total
        
        # Completeness: Are semantic types mostly found?
        inferred = sum(1 for c in columns if c['inferred_semantic_type'] != 'Unknown')
        completeness = inferred / total
        
        overall = (naming_quality + completeness) / 2
        
        return {
            "completeness_score": round(completeness, 2),
            "naming_quality_score": round(naming_quality, 2),
            "consistency_score": 1.0,  # Placeholder for deeper data profiling
            "normalization_score": 1.0,
            "relationship_score": 1.0, # Placeholder
            "overall_quality_score": round(overall, 2)
        }

    def register_schema(self, dataset_version_id: str, columns_metadata: List[Dict[str, Any]]) -> DatasetSchema:
        # Check if schema exists for this version, if so, delete to rebuild
        existing = self.db.query(DatasetSchema).filter(DatasetSchema.dataset_version_id == dataset_version_id).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()
            
        # Create Root
        schema = DatasetSchema(dataset_version_id=dataset_version_id)
        self.db.add(schema)
        self.db.flush()
        
        # Add Columns
        for col in columns_metadata:
            db_col = SchemaColumn(
                schema_id=schema.id,
                **col
            )
            self.db.add(db_col)
            
        # Hashes
        hashes = self.generate_hashes(columns_metadata)
        fingerprint = SchemaFingerprint(schema_id=schema.id, **hashes)
        self.db.add(fingerprint)
        
        # Quality
        quality_scores = self.calculate_quality(columns_metadata)
        quality = SchemaQuality(schema_id=schema.id, **quality_scores)
        self.db.add(quality)
        
        self.db.commit()
        return schema
        
    def get_schema_for_dataset(self, dataset_id: str):
        # We fetch the schema for the LATEST active version
        from app.models.dataset import DatasetVersion
        latest_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.is_active == True
        ).first()
        
        if not latest_version:
            return None
            
        return self.db.query(DatasetSchema).filter(DatasetSchema.dataset_version_id == latest_version.id).first()
