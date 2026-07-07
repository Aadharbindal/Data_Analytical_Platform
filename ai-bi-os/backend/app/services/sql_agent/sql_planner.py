from typing import List, Dict, Any
from app.schemas.sql_agent import SchemaMetadataResponse, BusinessGlossaryEntry

class SQLPlanner:
    def __init__(self):
        pass

    def plan_query(self, intent: str, schema: List[SchemaMetadataResponse], terms: List[BusinessGlossaryEntry]) -> Dict[str, Any]:
        """
        Drafts the execution plan: which tables to join, what to select, and how to aggregate.
        """
        plan = {
            "intent": intent,
            "target_tables": [],
            "select_columns": [],
            "joins": []
        }
        
        for term in terms:
            if term.mapped_table not in plan["target_tables"]:
                plan["target_tables"].append(term.mapped_table)
            if term.mapped_column:
                plan["select_columns"].append(f"{term.mapped_table}.{term.mapped_column}")
                
        # MVP fallback if no terms matched
        if not plan["target_tables"] and schema:
            plan["target_tables"].append(schema[0].table_name)
            plan["select_columns"].append("*")
            
        return plan
