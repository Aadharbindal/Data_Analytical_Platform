from typing import Dict, Any

class SQLGenerator:
    def __init__(self):
        pass

    def generate(self, plan: Dict[str, Any], dialect: str) -> str:
        """
        Builds the actual SQL string for the target dialect.
        """
        tables = ", ".join(plan["target_tables"])
        columns = ", ".join(plan["select_columns"])
        
        sql = f"SELECT {columns} FROM {tables}"
        
        if plan["intent"] == "Top N":
            if dialect == "duckdb" or dialect == "postgres":
                sql += " LIMIT 10"
            elif dialect == "sqlserver":
                sql = f"SELECT TOP 10 {columns} FROM {tables}"
                
        return sql
