import uuid
from typing import List, Dict, Any

class KnowledgeGraph:
    """Manages business entities and relationships across datasets."""
    
    def __init__(self):
        # In a real system, this connects to Neo4j or PostgreSQL (using recursive CTEs)
        self.nodes = {}
        self.edges = []
        
    def add_entity(self, entity_type: str, name: str, metadata: Dict[str, Any] = None) -> str:
        """Adds a business entity (e.g., 'Customer', 'Product', 'Revenue')."""
        node_id = str(uuid.uuid4())
        self.nodes[node_id] = {
            "type": entity_type,
            "name": name,
            "metadata": metadata or {}
        }
        return node_id
        
    def link_entities(self, source_id: str, target_id: str, relationship: str, weight: float = 1.0):
        """Creates a relationship between two entities."""
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append({
                "source": source_id,
                "target": target_id,
                "relationship": relationship,
                "weight": weight
            })
            return True
        return False

    def link_dataset_to_entity(self, dataset_id: str, column_name: str, entity_id: str):
        """Links a specific dataset column to a global business entity."""
        # This enables the AI to understand that 'Rev_2026' in Dataset A 
        # is the same business concept as 'Total_Revenue' in Dataset B.
        self.edges.append({
            "source": f"dataset:{dataset_id}:col:{column_name}",
            "target": entity_id,
            "relationship": "represents"
        })
        
    def get_related_entities(self, entity_id: str, max_depth: int = 1) -> List[Dict]:
        """Finds entities related to the given entity."""
        related = []
        for edge in self.edges:
            if edge["source"] == entity_id:
                related.append({
                    "entity": self.nodes.get(edge["target"]),
                    "relationship": edge["relationship"]
                })
        return related
