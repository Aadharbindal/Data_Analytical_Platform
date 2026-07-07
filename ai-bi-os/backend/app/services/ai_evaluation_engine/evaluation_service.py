import time
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.ai_evaluation_engine import (
    EvaluationObject, EvaluationMetric, Leaderboard, RegressionReport, EvaluationHistory
)
from app.schemas.ai_evaluation_engine import BenchmarkRequest
from app.repositories.ai_evaluation_engine_repository import AIEvaluationEngineRepository


def _deterministic_score(seed: str, lo: float, hi: float) -> float:
    """
    Produces a reproducible float in [lo, hi] seeded by an arbitrary string.
    Uses SHA-256 so the same seed always yields the same score — no randomness.
    """
    digest = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    normalized = (digest % 10_000) / 10_000.0       # 0.0 – 1.0
    return round(lo + normalized * (hi - lo), 4)


class MetricsCalculator:
    def calculate(self, seed: str = "default") -> Dict[str, float]:
        """
        Deterministic benchmark metrics based on the evaluation seed.
        The seed is typically: workspace_id + evaluation_type + target_module.
        """
        acc = _deterministic_score(seed + ":acc", 0.75, 0.98)
        f1  = _deterministic_score(seed + ":f1",  0.70, 0.97)
        grd = _deterministic_score(seed + ":grd", 0.80, 0.99)
        hlc = _deterministic_score(seed + ":hlc", 0.01, 0.15)
        lat = _deterministic_score(seed + ":lat", 200.0, 1500.0)
        cost = _deterministic_score(seed + ":cst", 0.001, 0.05)
        return {
            "Accuracy": acc,
            "F1 Score": f1,
            "Groundedness": grd,
            "Hallucination Rate": hlc,
            "Latency": lat,
            "Cost": cost
        }


class RegressionDetectionService:
    def detect(self, current_metrics: Dict[str, float], repository: AIEvaluationEngineRepository, workspace_id: str, eval_id: str):
        # Mock detection: if accuracy < 0.8, trigger regression
        acc = current_metrics.get("Accuracy", 1.0)
        if acc < 0.80:
            reg = RegressionReport(
                workspace_id=workspace_id,
                evaluation_id=eval_id,
                metric_name="Accuracy",
                previous_value=0.85,
                current_value=acc,
                degradation_percentage=round(((0.85 - acc) / 0.85) * 100, 2)
            )
            repository.add_regression(reg)

class LeaderboardEngine:
    def update(self, request: BenchmarkRequest, current_metrics: Dict[str, float], repository: AIEvaluationEngineRepository):
        acc = current_metrics.get("Accuracy", 0.0)
        
        entity = request.model_version if request.evaluation_type == "MODEL" else \
                 request.prompt_version if request.evaluation_type == "PROMPT" else \
                 request.target_module
                 
        if not entity:
            entity = "Unknown"
        
        # Deterministic ranking: higher accuracy == lower (better) rank number
        overall_rank = max(1, min(10, int((1.0 - acc) * 10) + 1))
            
        lb = Leaderboard(
            workspace_id=request.workspace_id,
            category=request.evaluation_type,
            entity_name=entity,
            aggregated_score=acc,
            overall_rank=overall_rank
        )
        repository.update_leaderboard(lb)

class EvaluationService:
    """Orchestrates the running of benchmarks and updating of telemetry."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AIEvaluationEngineRepository(db)
        self.calculator = MetricsCalculator()
        self.regression_detector = RegressionDetectionService()
        self.leaderboard_engine = LeaderboardEngine()

    def run_benchmark(self, request: BenchmarkRequest) -> EvaluationObject:
        # Build a deterministic seed from the request parameters
        seed = f"{request.workspace_id}:{request.evaluation_type}:{request.target_module}:{request.model_version}"
        metrics = self.calculator.calculate(seed=seed)
        
        # Aggregate scores out of 100
        quality_score = metrics["Accuracy"] * 100
        cost_score = max(0, 100 - (metrics["Cost"] * 1000)) # Mock normalization
        latency_score = max(0, 100 - (metrics["Latency"] / 20)) # Mock normalization
        overall_score = (quality_score * 0.6) + (cost_score * 0.2) + (latency_score * 0.2)
        
        eval_obj = EvaluationObject(
            workspace_id=request.workspace_id,
            suite_id=request.suite_id,
            evaluation_type=request.evaluation_type,
            target_module=request.target_module,
            model_version=request.model_version,
            prompt_version=request.prompt_version,
            quality_score=quality_score,
            cost_score=cost_score,
            latency_score=latency_score,
            overall_score=overall_score
        )
        eval_obj = self.repository.create_evaluation(eval_obj)
        
        for name, value in metrics.items():
            self.repository.add_metric(EvaluationMetric(
                evaluation_id=eval_obj.id,
                metric_name=name,
                metric_value=value
            ))
            
        self.regression_detector.detect(metrics, self.repository, request.workspace_id, eval_obj.id)
        self.leaderboard_engine.update(request, metrics, self.repository)
        
        self.repository.add_history(EvaluationHistory(
            workspace_id=request.workspace_id,
            event="BENCHMARK_COMPLETED",
            details=f"Suite run for {request.evaluation_type} finished."
        ))
        
        return eval_obj

    def list_evaluations(self) -> List[EvaluationObject]:
        return self.repository.list_evaluations()
        
    def get_leaderboards(self, workspace_id: str) -> Dict[str, List[Leaderboard]]:
        return {
            "MODEL": self.repository.list_leaderboard("MODEL", workspace_id),
            "PROMPT": self.repository.list_leaderboard("PROMPT", workspace_id),
            "WORKFLOW": self.repository.list_leaderboard("WORKFLOW", workspace_id),
        }
        
    def get_regressions(self, workspace_id: str) -> List[RegressionReport]:
        return self.repository.list_regressions(workspace_id)
