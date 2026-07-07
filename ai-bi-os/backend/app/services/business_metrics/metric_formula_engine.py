import logging

logger = logging.getLogger("MetricFormulaEngine")

class MetricFormulaEngine:
    """
    Translates user-defined mathematical formulas into DuckDB executable SQL strings.
    """
    
    def compile_to_sql(self, formula: str, dataset_table_name: str, dimension: str = None) -> str:
        """
        Converts a business metric formula into a full SQL query.
        E.g. formula: "SUM(sales) / COUNT(customers)"
        Output: "SELECT SUM(sales) / COUNT(customers) as value, Region FROM dataset_x GROUP BY Region"
        """
        # MVP: We assume the formula is already mostly valid SQL logic.
        # In prod, we'd replace metric references with their subqueries or pre-aggregated columns.
        
        select_clause = f"SELECT {formula} as value"
        
        if dimension:
            select_clause += f", {dimension}"
            
        sql = f"{select_clause} FROM {dataset_table_name}"
        
        if dimension:
            sql += f" GROUP BY {dimension}"
            
        return sql

metric_formula_engine = MetricFormulaEngine()
