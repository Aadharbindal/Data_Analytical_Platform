from typing import List, Dict, Any

class EntityEngine:
    """Identifies Fact/Dimension tables and core entities/metrics based on semantic columns."""
    
    METRICS_KEYWORDS = ["Revenue", "Profit", "Margin", "Value", "Quantity", "Tax", "Discount", "Cost", "Expense", "Salary"]
    ENTITY_KEYWORDS = ["Customer", "Product", "Order", "Invoice", "Employee", "Department", "Store", "Region"]
    
    @staticmethod
    def analyze(semantic_columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        entities = set()
        metrics = set()
        
        dimension_count = 0
        fact_count = 0
        id_count = 0
        
        for col in semantic_columns:
            name = col["business_name"]
            
            # Detect Metrics
            if any(k in name for k in EntityEngine.METRICS_KEYWORDS):
                metrics.add(name)
                col["column_type"] = "Fact"
                fact_count += 1
                
            # Detect Entities and Dimensions
            elif "Identifier" in name or "SKU" in name or name.endswith(" ID"):
                col["column_type"] = "ID"
                id_count += 1
                # Extract entity name (e.g., "Customer Identifier" -> "Customer")
                entity_name = name.replace(" Identifier", "").replace(" SKU", "")
                if entity_name in EntityEngine.ENTITY_KEYWORDS:
                    entities.add(entity_name)
                    
            elif any(k in name for k in EntityEngine.ENTITY_KEYWORDS):
                col["column_type"] = "Dimension"
                dimension_count += 1
                # Exact matches or containing matches
                for ek in EntityEngine.ENTITY_KEYWORDS:
                    if ek in name:
                        entities.add(ek)
                        
            else:
                col["column_type"] = "Dimension" # Default
                dimension_count += 1
                
        # Determine table type
        table_type = "Lookup Table"
        if fact_count > 0 and dimension_count > 0 and id_count > 0:
            table_type = "Fact Table"
        elif fact_count == 0 and dimension_count > 0 and id_count > 0:
            table_type = "Dimension Table"
        elif id_count >= 2 and fact_count == 0 and dimension_count == 0:
            table_type = "Bridge Table"
            
        return {
            "entities": list(entities),
            "metrics": list(metrics),
            "table_type": table_type,
            "annotated_columns": semantic_columns
        }
