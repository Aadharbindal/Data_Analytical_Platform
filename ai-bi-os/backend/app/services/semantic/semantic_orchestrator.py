from typing import List, Dict, Any

from app.services.semantic.alias_engine import AliasEngine
from app.services.semantic.entity_engine import EntityEngine
from app.services.semantic.domain_engine import DomainEngine
from app.services.semantic.ontology_engine import OntologyEngine

class SemanticOrchestrator:
    """Coordinates the semantic inference pipeline."""
    
    @staticmethod
    def evaluate_schema(schema_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        # 1. Alias Resolution
        annotated_columns = []
        for col in schema_metadata:
            business_name = AliasEngine.resolve_alias(col["original_header"])
            annotated_columns.append({
                "schema_column_id": col["id"],
                "original_header": col["original_header"],
                "business_name": business_name
            })
            
        # 2. Entity & Metric Extraction
        entity_analysis = EntityEngine.analyze(annotated_columns)
        
        # 3. Domain Inference
        domain = DomainEngine.infer_domain(entity_analysis["entities"], entity_analysis["metrics"])
        
        # 4. Ontology Generation
        ontology = OntologyEngine.build_graph(entity_analysis["entities"], entity_analysis["metrics"])
        
        return {
            "entity_analysis": entity_analysis,
            "domain": domain,
            "ontology": ontology
        }
