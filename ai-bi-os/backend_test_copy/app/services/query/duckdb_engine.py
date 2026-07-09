import duckdb
from typing import List, Dict, Any
from fastapi import HTTPException

class DuckDBEngine:
    """The core wrapper around the DuckDB in-memory execution environment."""
    
    def __init__(self):
        # We use an in-memory database to avoid locking.
        # It's fast enough to boot up instantly per request or pool.
        self.con = duckdb.connect(database=':memory:', read_only=False)
        
    def register_dataset(self, view_name: str, file_path: str, format: str = "csv"):
        """Registers a raw file as a virtual view in DuckDB."""
        try:
            if format == "csv":
                # DuckDB's read_csv_auto handles headers and types automatically
                self.con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_csv_auto('{file_path}')")
            elif format == "parquet":
                self.con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{file_path}')")
            elif format == "json":
                self.con.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_json_auto('{file_path}')")
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to register dataset view: {str(e)}")
            
    def execute(self, sql: str) -> Dict[str, Any]:
        """Executes a SQL query and returns results and schema."""
        try:
            # Execute query and get the result relation
            relation = self.con.sql(sql)
            if not relation:
                return {"schema": [], "rows": []}
                
            # Fetch as dictionary
            df = relation.df()
            
            # Build schema metadata based on returned columns
            schema = [{"name": col, "type": str(df[col].dtype)} for col in df.columns]
            
            # Convert NaN to None for JSON serialization
            df = df.replace({float('nan'): None})
            
            # Convert to list of dicts
            rows = df.to_dict(orient="records")
            
            return {
                "schema": schema,
                "rows": rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Query Execution Error: {str(e)}")
            
    def explain(self, sql: str) -> str:
        """Returns the execution plan."""
        try:
            res = self.con.execute(f"EXPLAIN {sql}").fetchall()
            return "\n".join([str(r) for r in res])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Explain Error: {str(e)}")
            
    def close(self):
        self.con.close()
