import time
import json
import traceback
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from app.repositories.python_agent import PythonExecutionRepository
from app.schemas.python_agent import WorkflowDefinitionSchema

class AnalysisValidator:
    """Validates workflows against strict security constraints."""
    ALLOWED_OPERATIONS = [
        "DROP_NULLS", 
        "FILL_NULLS", 
        "SCALE_FEATURES",
        "FIT_KMEANS", 
        "CALCULATE_CORRELATION",
        "SUMMARY_STATISTICS",
        "FILTER_ROWS",
        "GROUP_BY_AGGREGATE"
    ]

    @classmethod
    def validate(cls, workflow: WorkflowDefinitionSchema) -> tuple[bool, str]:
        for step in workflow.steps:
            if step.operation not in cls.ALLOWED_OPERATIONS:
                return False, f"Operation {step.operation} is not allowed."
        return True, "Valid"


class SandboxExecutor:
    """Executes a validated workflow deterministically."""
    
    def __init__(self):
        # We would use a memory-limited sandbox (like multiprocessing or resource limit)
        # For MVP, we map operations to safe functions directly.
        self.operations = {
            "DROP_NULLS": self._drop_nulls,
            "FILL_NULLS": self._fill_nulls,
            "SCALE_FEATURES": self._scale_features,
            "FIT_KMEANS": self._fit_kmeans,
            "CALCULATE_CORRELATION": self._calculate_correlation,
            "SUMMARY_STATISTICS": self._summary_statistics
        }

    def execute(self, df: pd.DataFrame, workflow: WorkflowDefinitionSchema) -> dict:
        results = {"artifacts": [], "trace": []}
        
        current_df = df.copy()
        
        for step in workflow.steps:
            operation = step.operation
            params = step.parameters
            
            start_t = time.time()
            if operation in self.operations:
                try:
                    current_df, step_artifact = self.operations[operation](current_df, params)
                    if step_artifact:
                        results["artifacts"].append(step_artifact)
                    
                    elapsed = int((time.time() - start_t) * 1000)
                    results["trace"].append(f"Executed {operation} in {elapsed}ms")
                except Exception as e:
                    results["trace"].append(f"Error in {operation}: {str(e)}\n{traceback.format_exc()}")
                    raise e
            else:
                raise ValueError(f"Unknown safe operation {operation}")
                
        results["final_df"] = current_df
        return results
        
    def _drop_nulls(self, df: pd.DataFrame, params: dict):
        cols = params.get("columns", None)
        df = df.dropna(subset=cols) if cols else df.dropna()
        return df, {"type": "REPORT", "name": "Drop Nulls", "data": {"rows_remaining": len(df)}}

    def _fill_nulls(self, df: pd.DataFrame, params: dict):
        value = params.get("value", 0)
        cols = params.get("columns", df.columns.tolist())
        for c in cols:
            df[c] = df[c].fillna(value)
        return df, None

    def _scale_features(self, df: pd.DataFrame, params: dict):
        cols = params.get("columns", [])
        if not cols:
            return df, None
        scaler = StandardScaler()
        df[cols] = scaler.fit_transform(df[cols])
        return df, None

    def _fit_kmeans(self, df: pd.DataFrame, params: dict):
        n_clusters = params.get("n_clusters", 3)
        cols = params.get("columns", [])
        if not cols:
            raise ValueError("Columns required for KMeans")
            
        model = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = model.fit_predict(df[cols])
        df["cluster"] = clusters
        
        # Output centroids as an artifact
        centroids = model.cluster_centers_
        
        artifact = {
            "type": "MODEL_METRICS",
            "name": "KMeans Clustering Results",
            "data": {
                "n_clusters": n_clusters,
                "centroids": centroids.tolist()
            }
        }
        return df, artifact

    def _calculate_correlation(self, df: pd.DataFrame, params: dict):
        method = params.get("method", "pearson")
        cols = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
        corr = df[cols].corr(method=method)
        
        artifact = {
            "type": "TABLE",
            "name": "Correlation Matrix",
            "data": corr.to_dict()
        }
        return df, artifact

    def _summary_statistics(self, df: pd.DataFrame, params: dict):
        cols = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
        stats = df[cols].describe().to_dict()
        
        artifact = {
            "type": "TABLE",
            "name": "Summary Statistics",
            "data": stats
        }
        return df, artifact


class PythonAgentService:
    """Orchestrates validation, execution, and persistence."""
    
    def __init__(self, repository: PythonExecutionRepository):
        self.repo = repository
        self.validator = AnalysisValidator()
        self.executor = SandboxExecutor()
        
    def execute_workflow(self, workspace_id: str, workflow_def: WorkflowDefinitionSchema, df: pd.DataFrame = None):
        # Validate
        is_safe, reason = self.validator.validate(workflow_def)
        
        # Save workflow
        workflow = self.repo.create_workflow(
            workspace_id=workspace_id,
            intent=workflow_def.intent,
            parameters={},
            steps=[s.model_dump() for s in workflow_def.steps]
        )
        
        # Create execution
        execution = self.repo.create_execution(workflow.id)
        
        self.repo.save_validation(execution.id, is_safe, reason)
        
        if not is_safe:
            self.repo.update_execution_status(execution.id, "FAILED", f"Validation failed: {reason}")
            return execution
            
        self.repo.update_execution_status(execution.id, "EXECUTING")
        
        # Execute
        start_time = time.time()
        
        # In a real system, df would be loaded from dataset_id. Using mock df if not passed
        if df is None:
            df = pd.DataFrame(np.random.rand(100, 4), columns=['A', 'B', 'C', 'D'])
            
        try:
            results = self.executor.execute(df, workflow_def)
            
            # Save artifacts
            for art in results["artifacts"]:
                # Content URI would be an S3 path, but inline JSON for MVP
                content_uri = json.dumps(art["data"]) 
                self.repo.save_artifact(execution.id, art["type"], art["name"], content_uri)
                
            trace_str = "\n".join(results["trace"])
            self.repo.save_log(execution.id, trace_str)
            
            end_time = time.time()
            exec_time_ms = int((end_time - start_time) * 1000)
            
            # Save metrics
            self.repo.save_metrics(execution.id, exec_time_ms, 0, 0) # memory/cpu mocked
            
            self.repo.update_execution_status(execution.id, "COMPLETED")
            
        except Exception as e:
            self.repo.save_log(execution.id, f"FAILED: {str(e)}\n{traceback.format_exc()}")
            self.repo.update_execution_status(execution.id, "FAILED", str(e))
            
        return self.repo.get_execution(execution.id)
