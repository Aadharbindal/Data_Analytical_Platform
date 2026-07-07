from typing import List
from sqlalchemy.orm import Session
from app.models.recommendation import Recommendation, ActionPlan, ActionStep

class ActionPlanningEngine:
    """Constructs the step-by-step roadmap for a recommendation using templates."""
    
    @staticmethod
    def plan_actions(recommendations: List[Recommendation]) -> None:
        for rec in recommendations:
            plan = ActionPlan(
                title=f"Execution Plan: {rec.title}",
                business_objective=f"Address {rec.category} in {rec.business_domain}",
                expected_outcome="Mitigate risk or capture opportunity identified by the decision engine.",
                success_metrics={"primary": "Resolution of triggering condition"}
            )
            rec.action_plan = plan
            
            # Deterministic standard template
            step1 = ActionStep(
                order_index=1,
                title="Review Triggering Insights",
                description="Investigate the underlying analytics that triggered this recommendation.",
                estimated_duration="1 Day",
                difficulty="LOW"
            )
            
            step2 = ActionStep(
                order_index=2,
                title="Draft Execution Strategy",
                description="Formulate a specific response plan based on the domain.",
                estimated_duration="3 Days",
                difficulty="MEDIUM",
                prerequisites=["Review Triggering Insights"]
            )
            
            step3 = ActionStep(
                order_index=3,
                title="Implement & Monitor",
                description="Execute the strategy and monitor the KPI for reversal.",
                estimated_duration="2 Weeks",
                difficulty="HIGH",
                dependencies=["Draft Execution Strategy"]
            )
            
            plan.steps.extend([step1, step2, step3])
