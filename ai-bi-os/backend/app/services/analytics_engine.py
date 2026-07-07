import pandas as pd
from typing import Dict, Any, List
# from app.services.duckdb_engine import DuckDBEngine

class AnalyticsEngine:
    """Deterministic analytics engine using DuckDB for high-performance aggregations."""
    
    def __init__(self, duckdb_engine: Any):
        self.db = duckdb_engine
        
    def generate_descriptive_stats(self, table_name: str, columns: List[str]) -> Dict[str, Any]:
        """Calculates MIN, MAX, AVG, SUM, and COUNT for given columns."""
        stats = {}
        for col in columns:
            query = f"""
            SELECT 
                MIN({col}) as min_val,
                MAX({col}) as max_val,
                AVG({col}) as avg_val,
                SUM({col}) as sum_val,
                COUNT({col}) as count_val
            FROM {table_name}
            """
            try:
                result = self.db.execute_query(query)
                if not result.empty:
                    stats[col] = result.iloc[0].to_dict()
                else:
                    stats[col] = {"min": 0, "max": 0, "avg": 0, "sum": 0, "count": 0}
            except Exception as e:
                # DuckDB error (e.g. table not found)
                stats[col] = {"error": str(e)}
        return stats
        
    def calculate_kpis(self, table_name: str, dimensions: List[str], metrics: List[str]) -> pd.DataFrame:
        """Groups by dimensions and aggregates metrics to form KPIs."""
        dims = ", ".join(dimensions)
        aggs = ", ".join([f"SUM({m}) as total_{m}" for m in metrics])
        
        query = f"""
        SELECT {dims}, {aggs}
        FROM {table_name}
        GROUP BY {dims}
        ORDER BY total_{metrics[0]} DESC
        """
        try:
            return self.db.execute_query(query)
        except Exception:
            return pd.DataFrame()

    def build_correlation_matrix(self, table_name: str, numeric_columns: List[str]) -> pd.DataFrame:
        """Calculates Pearson correlation between numeric columns."""
        # DuckDB has corr(x,y), but for a full matrix, pandas is usually easier after fetching data
        try:
            query = f"SELECT {', '.join(numeric_columns)} FROM {table_name}"
            df = self.db.execute_query(query)
            return df.corr()
        except Exception:
            return pd.DataFrame()
