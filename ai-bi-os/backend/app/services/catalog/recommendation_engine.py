from sqlalchemy.orm import Session
from app.models.semantic import BusinessEntity
from app.models.catalog import CatalogRecommendation, MetadataCatalog

class RecommendationEngine:
    """Generates catalog-level recommendations like Join Candidates."""
    
    @staticmethod
    def generate_recommendations(db: Session, catalog_id: str, dataset_id: str, version_id: str):
        # Find entities in this dataset
        my_entities = db.query(BusinessEntity.entity_name).filter(BusinessEntity.dataset_version_id == version_id).all()
        my_entity_names = {e[0] for e in my_entities}
        
        if not my_entity_names:
            return
            
        # Find other catalogs
        other_catalogs = db.query(MetadataCatalog).filter(MetadataCatalog.id != catalog_id).all()
        
        for other in other_catalogs:
            other_entities = db.query(BusinessEntity.entity_name).filter(BusinessEntity.dataset_version_id == other.dataset_version_id).all()
            other_entity_names = {e[0] for e in other_entities}
            
            overlap = my_entity_names.intersection(other_entity_names)
            if overlap:
                rec = CatalogRecommendation(
                    catalog_id=catalog_id,
                    recommendation_type="Join Candidate",
                    target_dataset_id=other.dataset_id,
                    reasoning=f"Both datasets share the following business entities: {', '.join(overlap)}."
                )
                db.add(rec)
                
        db.commit()
