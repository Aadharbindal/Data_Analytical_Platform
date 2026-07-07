import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.decision_intelligence import (
    DecisionObject, DecisionReference, DecisionScenario, DecisionComparison,
    DecisionPolicy, DecisionApproval, DecisionHistory, DecisionMetrics
)
from app.schemas.decision_intelligence import DecisionGenerateRequest
from app.repositories.decision_intelligence_repository import DecisionIntelligenceRepository

class DecisionValidator:
    """Validates inputs before generation, ensuring no hallucinations."""
    def validate(self, request: DecisionGenerateRequest) -> bool:
        if not request.recommendation_ids:
            raise ValueError("Cannot generate decision: No source Recommendation provided.")
        return True

class DecisionOptimizer:
    """Simulates optimization of a decision based on constraints."""
    def optimize(self, request: DecisionGenerateRequest) -> tuple[float, float, str, int]:
        # Mock logic
        roi = 320.0
        risk = "LOW"
        priority = 1
        confidence = 0.95
        
        if request.business_objective.lower() == "minimize risk":
            roi = 150.0
            risk = "LOW"
        elif request.business_objective.lower() == "maximize roi":
            roi = 450.0
            risk = "HIGH"
            
        return roi, confidence, risk, priority

class DecisionPlanner:
    """Simulates the construction of scenarios and comparisons."""
    def generate_matrix(self) -> tuple[List[Dict], List[Dict], List[Dict]]:
        scenarios = [
            {"scenario_type": "EXPECTED", "description": "Baseline growth with new strategy.", "financial_projection": 200000.0},
            {"scenario_type": "OPTIMISTIC", "description": "High adoption rate in target market.", "financial_projection": 500000.0},
            {"scenario_type": "CONSERVATIVE", "description": "Delayed execution impact.", "financial_projection": 50000.0}
        ]
        
        comparisons = [
            {"strategy_name": "Aggressive Expansion", "description": "Expand to all regions immediately.", "estimated_roi": 450.0, "risk_level": "HIGH"},
            {"strategy_name": "Phased Rollout", "description": "Start with top 2 regions.", "estimated_roi": 320.0, "risk_level": "LOW"}
        ]
        
        policies = [
            {"policy_name": "Risk Threshold Policy", "constraint_type": "RISK", "constraint_value": "MAX_MEDIUM", "is_satisfied": True},
            {"policy_name": "Budget Cap", "constraint_type": "BUDGET", "constraint_value": "$500,000", "is_satisfied": True}
        ]
        
        return scenarios, comparisons, policies

class DecisionManager:
    """High-level orchestrator service."""
    def __init__(self, db: Session):
        self.db = db
        self.repository = DecisionIntelligenceRepository(db)
        self.validator = DecisionValidator()
        self.optimizer = DecisionOptimizer()
        self.planner = DecisionPlanner()

    def generate_decision(self, request: DecisionGenerateRequest) -> DecisionObject:
        start_time = time.time()
        
        self.validator.validate(request)
        
        roi, confidence, risk, priority = self.optimizer.optimize(request)
        scenarios_data, comparisons_data, policies_data = self.planner.generate_matrix()
        
        dec = DecisionObject(
            workspace_id=request.workspace_id,
            dataset_id=request.dataset_id,
            decision_type=request.decision_type,
            business_objective=request.business_objective,
            decision_summary=f"Executing Phased Rollout strategy to {request.business_objective.lower()}.",
            selected_strategy="Phased Rollout",
            expected_roi=roi,
            expected_revenue_impact=roi * 1000,
            expected_cost_impact=50000.0,
            expected_risk=risk,
            confidence_score=confidence,
            business_priority=priority,
            approval_status="DRAFT"
        )
        created = self.repository.create_decision(dec)
        
        for s_data in scenarios_data:
            self.repository.add_scenario(DecisionScenario(decision_id=created.id, **s_data))
            
        for c_data in comparisons_data:
            self.repository.add_comparison(DecisionComparison(decision_id=created.id, **c_data))
            
        for p_data in policies_data:
            self.repository.add_policy(DecisionPolicy(decision_id=created.id, **p_data))
            
        for r_id in request.recommendation_ids:
            self.repository.add_reference(DecisionReference(decision_id=created.id, reference_type="RECOMMENDATION", reference_id=r_id))
            
        self.repository.add_history(DecisionHistory(decision_id=created.id, event="GENERATED"))
        
        latency = int((time.time() - start_time) * 1000)
        self.repository.log_metrics(DecisionMetrics(
            workspace_id=request.workspace_id,
            generation_time_ms=latency,
            confidence=confidence,
            roi=roi
        ))
        
        return created

    def get_decision(self, decision_id: str) -> Optional[DecisionObject]:
        return self.repository.get_decision(decision_id)
        
    def list_by_workspace(self, workspace_id: str) -> List[DecisionObject]:
        return self.repository.list_decisions(workspace_id)
