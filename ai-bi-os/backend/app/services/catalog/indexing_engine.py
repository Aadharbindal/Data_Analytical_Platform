from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.catalog import CatalogSearchIndex
from app.models.dataset import Dataset
from app.models.schema import DatasetSchema, SchemaColumn
from app.models.semantic import SemanticDomain, BusinessEntity, SemanticColumn

class IndexingEngine:
    """Builds a high-performance tokenized search index."""
    
    @staticmethod
    def build_index(db: Session, dataset_id: str, version_id: str):
        # Clear old index for this dataset
        db.query(CatalogSearchIndex).filter(CatalogSearchIndex.dataset_id == dataset_id).delete()
        
        tokens_to_insert = []
        
        # 1. Dataset Name and Description (Weight 10)
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            for word in dataset.name.lower().replace("_", " ").replace("-", " ").split():
                tokens_to_insert.append(CatalogSearchIndex(dataset_id=dataset_id, token=word, token_type="DatasetName", weight=10))
                
        # 2. Schema Columns (Weight 5)
        schema = db.query(DatasetSchema).filter(DatasetSchema.dataset_version_id == version_id).first()
        if schema:
            for col in schema.columns:
                for word in col.original_header.lower().replace("_", " ").split():
                    tokens_to_insert.append(CatalogSearchIndex(dataset_id=dataset_id, token=word, token_type="ColumnName", weight=5))
                    
        # 3. Semantic Business Entities (Weight 8)
        entities = db.query(BusinessEntity).filter(BusinessEntity.dataset_version_id == version_id).all()
        for ent in entities:
            for word in ent.entity_name.lower().split():
                tokens_to_insert.append(CatalogSearchIndex(dataset_id=dataset_id, token=word, token_type="SemanticEntity", weight=8))
                
        # 4. Semantic Domains (Weight 6)
        domain = db.query(SemanticDomain).filter(SemanticDomain.dataset_version_id == version_id).first()
        if domain:
            for word in domain.primary_domain.lower().split():
                tokens_to_insert.append(CatalogSearchIndex(dataset_id=dataset_id, token=word, token_type="SemanticDomain", weight=6))
                
        # 5. Semantic Columns (Weight 7)
        sem_cols = db.query(SemanticColumn).filter(SemanticColumn.dataset_version_id == version_id).all()
        for scol in sem_cols:
            for word in scol.business_name.lower().split():
                tokens_to_insert.append(CatalogSearchIndex(dataset_id=dataset_id, token=word, token_type="SemanticColumn", weight=7))
                
        # Bulk Insert
        if tokens_to_insert:
            db.bulk_save_objects(tokens_to_insert)
            db.commit()
