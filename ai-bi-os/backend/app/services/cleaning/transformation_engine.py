import polars as pl
from typing import List, Dict, Any

class TransformationEngine:
    """Core Engine executing transformation steps via Polars."""
    
    @staticmethod
    def execute_pipeline(df: pl.DataFrame, steps: List[Dict[str, Any]]) -> pl.DataFrame:
        """
        Executes a sequence of steps on a Polars DataFrame.
        Steps format: [{"operation_type": "TRIM_WHITESPACE", "target_column": "City", "parameters": {}}]
        """
        for step in steps:
            op = step.get("operation_type")
            col = step.get("target_column")
            params = step.get("parameters", {})
            
            if op == "TRIM_WHITESPACE" and col:
                df = df.with_columns(pl.col(col).str.strip_chars())
                
            elif op == "LOWERCASE" and col:
                df = df.with_columns(pl.col(col).str.to_lowercase())
                
            elif op == "UPPERCASE" and col:
                df = df.with_columns(pl.col(col).str.to_uppercase())
                
            elif op == "FILL_NULLS" and col:
                strategy = params.get("strategy", "constant")
                if strategy == "constant":
                    val = params.get("value", "")
                    df = df.with_columns(pl.col(col).fill_null(val))
                elif strategy == "mean":
                    df = df.with_columns(pl.col(col).fill_null(pl.col(col).mean()))
                elif strategy == "median":
                    df = df.with_columns(pl.col(col).fill_null(pl.col(col).median()))
                elif strategy == "mode":
                    # For simplicity, filling with the first mode
                    mode_val = df.select(pl.col(col).mode().first()).item()
                    df = df.with_columns(pl.col(col).fill_null(mode_val))
                    
            elif op == "DROP_DUPLICATES":
                if col:
                    df = df.unique(subset=[col])
                else:
                    df = df.unique()
                    
            elif op == "DROP_COLUMN" and col:
                if col in df.columns:
                    df = df.drop(col)
                    
            elif op == "RENAME_COLUMN" and col:
                new_name = params.get("new_name")
                if new_name:
                    df = df.rename({col: new_name})
                    
            elif op == "ABSOLUTE_VALUE" and col:
                df = df.with_columns(pl.col(col).abs())

            elif op == "CONSTANT_VALUE" and col:
                 df = df.with_columns(pl.lit(params.get("value")).alias(col))
                 
            # Note: For production, we'd wrap these in try-except and collect errors to fail the pipeline gracefully.
            
        return df
