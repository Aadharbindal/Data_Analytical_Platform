from typing import List
from app.models.recommendation import Recommendation, ImpactEstimation, ScenarioAnalysis

class ImpactEstimator:
    """Calculates expected financial/operational impact scenarios deterministically."""
    
    @staticmethod
    def estimate(recommendations: List[Recommendation]) -> None:
        for rec in recommendations:
            # Deterministic heuristic impact
            est = ImpactEstimation(
                revenue_increase=10000.0 if rec.category == "REVENUE_GROWTH" else 0,
                cost_reduction=5000.0 if rec.category == "COST_OPTIMIZATION" else 0,
                risk_reduction=0.8 if rec.severity in ["CRITICAL", "HIGH"] else 0.2
            )
            rec.impact_estimation = est
            rec.roi_estimate = (est.revenue_increase + est.cost_reduction) * est.risk_reduction
            
            # Scenarios
            expected = ScenarioAnalysis(
                scenario_type="EXPECTED_CASE",
                description="Standard execution without major blockers.",
                estimated_roi=rec.roi_estimate
            )
            worst = ScenarioAnalysis(
                scenario_type="WORST_CASE",
                description="Execution delayed or market conditions worsen.",
                estimated_roi=rec.roi_estimate * 0.2
            )
            best = ScenarioAnalysis(
                scenario_type="BEST_CASE",
                description="Perfect execution with synergistic effects.",
                estimated_roi=rec.roi_estimate * 1.5
            )
            rec.scenarios.extend([worst, expected, best])
