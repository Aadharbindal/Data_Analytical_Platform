import os
import pandas as pd
import logging
import duckdb

logger = logging.getLogger(__name__)

class DuckDBEngine:
    """Manages DuckDB connections and data loading."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        
    def mount_parquet(self, table_name: str, file_path: str):
        """Mounts a Parquet file to DuckDB as a view/table."""
        query = f"CREATE VIEW {table_name} AS SELECT * FROM read_parquet('{file_path}')"
        self.conn.execute(query)
        logger.info(f"Mounted Parquet file {file_path} as {table_name}")

    def load_dataframe(self, table_name: str, df: pd.DataFrame, persist_path: str = None):
        """Loads a Pandas DataFrame into DuckDB, optionally saving as Parquet first."""
        if persist_path:
            # Save to parquet for persistence
            df.to_parquet(persist_path)
            self.mount_parquet(table_name, persist_path)
        else:
            self.conn.register(table_name, df)
            logger.info(f"Registered DataFrame as {table_name} in memory")

    def execute_query(self, query: str) -> pd.DataFrame:
        """Executes a SQL query against DuckDB and returns a Pandas DataFrame."""
        logger.info(f"Executing Query: {query}")
        return self.conn.execute(query).fetchdf()
