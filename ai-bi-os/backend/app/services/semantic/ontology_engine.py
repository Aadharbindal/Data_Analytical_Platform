from typing import List, Dict, Any

class OntologyEngine:
    """Constructs a business ontology graph (Nodes & Edges) from detected entities."""
    
    # Pre-defined common business relationships
    RELATIONSHIPS = {
        ("Customer", "Order"): "Places",
        ("Order", "Product"): "Contains",
        ("Order", "Invoice"): "Generates",
        ("Product", "Category"): "Belongs To",
        ("Store", "Region"): "Located In",
        ("Employee", "Department"): "Works In",
        ("Employee", "Order"): "Processes",
        ("Customer", "Transaction"): "Executes",
        ("Transaction", "Account"): "Affects",
        ("Account", "Branch"): "Held At"
    }
    
    @staticmethod
    def build_graph(entities: List[str], metrics: List[str]) -> Dict[str, Any]:
        nodes = []
        edges = []
        
        # Add Entities as Nodes
        for e in entities:
            nodes.append({"label": e, "type": "Entity"})
            
        # Add Metrics as Nodes
        for m in metrics:
            nodes.append({"label": m, "type": "Metric"})
            
        # Attempt to draw edges between Entities based on known relationships
        for i in range(len(entities)):
            for j in range(len(entities)):
                if i == j:
                    continue
                e1 = entities[i]
                e2 = entities[j]
                
                # Check directional known relationships
                rel = OntologyEngine.RELATIONSHIPS.get((e1, e2))
                if rel:
                    edges.append({
                        "source": e1,
                        "target": e2,
                        "relation": rel
                    })
                    
        # Connect Metrics to their likely parent Fact entities (Simple heuristic: Metrics relate to the 'Event' entities like Order or Transaction)
        event_entities = [e for e in entities if e in ["Order", "Invoice", "Transaction", "Encounter"]]
        if event_entities:
            primary_event = event_entities[0]
            for m in metrics:
                edges.append({
                    "source": primary_event,
                    "target": m,
                    "relation": "Measures"
                })
        elif entities and metrics:
            # Fallback: connect metrics to the primary dimension
            for m in metrics:
                edges.append({
                    "source": entities[0],
                    "target": m,
                    "relation": "Measures"
                })
                
        return {
            "nodes": nodes,
            "edges": edges
        }
