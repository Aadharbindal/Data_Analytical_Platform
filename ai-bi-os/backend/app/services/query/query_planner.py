from app.services.query.duckdb_engine import DuckDBEngine

class QueryPlanner:
    """Generates the logical execution plan for a query."""
    
    @staticmethod
    def get_plan(sql: str, engine: DuckDBEngine) -> str:
        # DuckDB handles its own cost-based optimizations, projection pushdown,
        # join reordering, and predicate pushdowns natively via EXPLAIN.
        return engine.explain(sql)
