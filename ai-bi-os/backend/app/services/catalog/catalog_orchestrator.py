from sqlalchemy.orm import Session
from datetime import datetime

from app.models.catalog import MetadataCatalog
from app.services.catalog.indexing_engine import IndexingEngine
from app.services.catalog.scoring_engine import ScoringEngine
from app.services.catalog.documentation_engine import DocumentationEngine
from app.services.catalog.recommendation_engine import RecommendationEngine

class CatalogOrchestrator:
    """Coordinates the unified catalog update."""
    
    @staticmethod
    def process_catalog(db: Session, dataset_id: str, version_id: str):
        # 1. Ensure Catalog Object exists
        catalog = db.query(MetadataCatalog).filter(MetadataCatalog.dataset_id == dataset_id).first()
        if not catalog:
            catalog = MetadataCatalog(dataset_id=dataset_id)
            db.add(catalog)
            
        catalog.dataset_version_id = version_id
        catalog.last_indexed_at = datetime.utcnow()
        db.commit()
        
        # 2. Build Search Index
        IndexingEngine.build_index(db, dataset_id, version_id)
        
        # 3. Calculate Scores (Quality, Trust, etc)
        # Clear old score
        from app.models.catalog import CatalogScore, DatasetDocumentation, CatalogRecommendation
        db.query(CatalogScore).filter(CatalogScore.catalog_id == catalog.id).delete()
        db.query(DatasetDocumentation).filter(DatasetDocumentation.catalog_id == catalog.id).delete()
        db.query(CatalogRecommendation).filter(CatalogRecommendation.catalog_id == catalog.id).delete()
        db.commit()
        
        ScoringEngine.calculate_scores(db, catalog.id, version_id)
        
        # 4. Generate Documentation
        DocumentationEngine.generate_documentation(db, catalog.id, dataset_id, version_id)
        
        # 5. Generate Recommendations
        RecommendationEngine.generate_recommendations(db, catalog.id, dataset_id, version_id)
        
        return catalog.id
