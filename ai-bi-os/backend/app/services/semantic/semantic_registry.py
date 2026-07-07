from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.semantic import (
    SemanticDomain, BusinessEntity, SemanticMetric, SemanticColumn,
    BusinessGlossary, OntologyNode, OntologyEdge, SemanticRecommendation
)
from app.models.dataset import DatasetVersion

class SemanticRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def save_semantic_data(self, dataset_version_id: str, results: Dict[str, Any]):
        # Clear existing
        self.db.query(SemanticDomain).filter(SemanticDomain.dataset_version_id == dataset_version_id).delete()
        self.db.query(BusinessGlossary).filter(BusinessGlossary.dataset_version_id == dataset_version_id).delete()
        self.db.query(OntologyEdge).filter(OntologyEdge.dataset_version_id == dataset_version_id).delete()
        self.db.query(OntologyNode).filter(OntologyNode.dataset_version_id == dataset_version_id).delete()
        self.db.query(SemanticColumn).filter(SemanticColumn.dataset_version_id == dataset_version_id).delete()
        self.db.query(BusinessEntity).filter(BusinessEntity.dataset_version_id == dataset_version_id).delete()
        self.db.query(SemanticMetric).filter(SemanticMetric.dataset_version_id == dataset_version_id).delete()
        self.db.query(SemanticRecommendation).filter(SemanticRecommendation.dataset_version_id == dataset_version_id).delete()
        self.db.flush()
        
        # 1. Domain
        dom_data = results.get("domain", {})
        dom = SemanticDomain(
            dataset_version_id=dataset_version_id,
            primary_domain=dom_data.get("primary_domain", "General Business"),
            confidence_score=dom_data.get("confidence_score", 0.0),
            matched_rules=dom_data.get("matched_rules", [])
        )
        self.db.add(dom)
        
        # 2. Entities & Metrics
        entity_data = results.get("entity_analysis", {})
        entities = {}
        for e_name in entity_data.get("entities", []):
            ent = BusinessEntity(dataset_version_id=dataset_version_id, entity_name=e_name, confidence_score=0.9)
            self.db.add(ent)
            entities[e_name] = ent
            
        metrics = {}
        for m_name in entity_data.get("metrics", []):
            met = SemanticMetric(dataset_version_id=dataset_version_id, metric_name=m_name, confidence_score=0.9)
            self.db.add(met)
            metrics[m_name] = met
            
        self.db.flush()
        
        # 3. Semantic Columns
        for col in entity_data.get("annotated_columns", []):
            b_name = col["business_name"]
            ent_id = entities[b_name].id if b_name in entities else None
            met_id = metrics[b_name].id if b_name in metrics else None
            
            scol = SemanticColumn(
                dataset_version_id=dataset_version_id,
                schema_column_id=col["schema_column_id"],
                business_entity_id=ent_id,
                business_metric_id=met_id,
                column_type=col.get("column_type", "Dimension"),
                business_name=b_name,
                confidence_score=0.95
            )
            self.db.add(scol)
            
        # 4. Ontology
        ont_data = results.get("ontology", {})
        nodes = {}
        for n in ont_data.get("nodes", []):
            node = OntologyNode(
                dataset_version_id=dataset_version_id,
                node_label=n["label"],
                node_type=n["type"]
            )
            self.db.add(node)
            nodes[n["label"]] = node
            
            # Auto-gen glossary
            glos = BusinessGlossary(
                dataset_version_id=dataset_version_id,
                term=n["label"],
                definition=f"Automatically inferred {n['type'].lower()} representing {n['label']} within the {dom.primary_domain} domain."
            )
            self.db.add(glos)
            
        self.db.flush()
        
        for e in ont_data.get("edges", []):
            src = nodes.get(e["source"])
            tgt = nodes.get(e["target"])
            if src and tgt:
                edge = OntologyEdge(
                    dataset_version_id=dataset_version_id,
                    source_node_id=src.id,
                    target_node_id=tgt.id,
                    relation_name=e["relation"]
                )
                self.db.add(edge)
                
        # 5. Recommendations
        for m_name in metrics.keys():
            if m_name == "Revenue" or m_name == "Gross Merchandise Value":
                rec = SemanticRecommendation(dataset_version_id=dataset_version_id, recommendation_text="Revenue Forecasting is supported.", capability="Forecasting")
                self.db.add(rec)
            if m_name == "Margin" or m_name == "Profit":
                rec = SemanticRecommendation(dataset_version_id=dataset_version_id, recommendation_text="Profitability Analysis is possible.", capability="Analytics")
                self.db.add(rec)
        if "Customer" in entities and "Order" in entities:
            rec = SemanticRecommendation(dataset_version_id=dataset_version_id, recommendation_text="Customer Lifetime Value (CLV) is possible.", capability="AI")
            self.db.add(rec)
            
        self.db.commit()

    def get_semantic_data(self, dataset_id: str) -> Dict[str, Any]:
        latest_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.is_active == True
        ).first()
        
        if not latest_version:
            return {}
            
        vid = latest_version.id
        
        domain = self.db.query(SemanticDomain).filter(SemanticDomain.dataset_version_id == vid).first()
        entities = self.db.query(BusinessEntity).filter(BusinessEntity.dataset_version_id == vid).all()
        metrics = self.db.query(SemanticMetric).filter(SemanticMetric.dataset_version_id == vid).all()
        columns = self.db.query(SemanticColumn).filter(SemanticColumn.dataset_version_id == vid).all()
        glossary = self.db.query(BusinessGlossary).filter(BusinessGlossary.dataset_version_id == vid).all()
        nodes = self.db.query(OntologyNode).filter(OntologyNode.dataset_version_id == vid).all()
        edges = self.db.query(OntologyEdge).filter(OntologyEdge.dataset_version_id == vid).all()
        recs = self.db.query(SemanticRecommendation).filter(SemanticRecommendation.dataset_version_id == vid).all()
        
        return {
            "domain": domain,
            "entities": entities,
            "metrics": metrics,
            "columns": columns,
            "glossary": glossary,
            "nodes": nodes,
            "edges": edges,
            "recommendations": recs
        }
