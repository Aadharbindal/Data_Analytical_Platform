from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.schema import DatasetSchema
from app.models.semantic import SemanticDomain, BusinessEntity, SemanticMetric
from app.models.catalog import DatasetDocumentation

class DocumentationEngine:
    """Generates Markdown summaries from metadata."""
    
    @staticmethod
    def generate_documentation(db: Session, catalog_id: str, dataset_id: str, version_id: str):
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        schema = db.query(DatasetSchema).filter(DatasetSchema.dataset_version_id == version_id).first()
        domain = db.query(SemanticDomain).filter(SemanticDomain.dataset_version_id == version_id).first()
        entities = db.query(BusinessEntity).filter(BusinessEntity.dataset_version_id == version_id).all()
        metrics = db.query(SemanticMetric).filter(SemanticMetric.dataset_version_id == version_id).all()
        
        dom_name = domain.primary_domain if domain else "Unknown Domain"
        ent_names = ", ".join([e.entity_name for e in entities]) if entities else "None"
        met_names = ", ".join([m.metric_name for m in metrics]) if metrics else "None"
        
        business_summary = f"""# {dataset.name}

## Business Overview
This dataset belongs to the **{dom_name}** domain.
It tracks the following core business entities: **{ent_names}**.

## Key Performance Indicators
The system automatically identified the following metrics that can be calculated from this data: **{met_names}**.
"""

        row_count = schema.row_count if schema else 0
        col_count = len(schema.columns) if schema else 0
        
        technical_summary = f"""## Technical Specifications
- **Rows:** {row_count:,}
- **Columns:** {col_count}
- **Primary Entities:** {len(entities)}
- **Facts (Metrics):** {len(metrics)}
"""
        
        kpis = [m.metric_name for m in metrics]
        
        doc = DatasetDocumentation(
            catalog_id=catalog_id,
            business_summary=business_summary,
            technical_summary=technical_summary,
            recommended_kpis=kpis
        )
        db.add(doc)
        db.commit()
