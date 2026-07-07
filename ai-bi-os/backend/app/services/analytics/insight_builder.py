from typing import List
from app.models.analytics import AnalyticsBusinessMetric, TrendAnalysis, SegmentAnalysis, VarianceAnalysis, CorrelationAnalysis, InsightObject

class InsightBuilder:
    """Generates structured InsightObjects from the raw analytics output."""
    
    @staticmethod
    def build_insights(run_id: str, metrics: List[AnalyticsBusinessMetric], trends: List[TrendAnalysis], segments: List[SegmentAnalysis], variances: List[VarianceAnalysis], correlations: List[CorrelationAnalysis]) -> List[InsightObject]:
        insights = []
        
        # 1. Trend Insights
        for t in trends:
            if t.slope and t.slope > 1.0:
                insights.append(InsightObject(
                    run_id=run_id,
                    title=f"{t.metric_name} is Growing",
                    description=f"Detected a positive {t.trend_direction.lower()} trend in {t.metric_name} over time.",
                    metric=t.metric_name,
                    evidence_data={"slope": t.slope, "confidence": t.confidence},
                    calculation_method="Time-Series Linear Regression",
                    severity="LOW",
                    confidence=t.confidence
                ))
                
        # 2. Segment Insights (e.g. Pareto Principle)
        for s in segments:
            if s.percentage_of_total and s.percentage_of_total > 40.0:
                 insights.append(InsightObject(
                    run_id=run_id,
                    title=f"High Concentration in {s.dimension}",
                    description=f"Segment '{s.segment_value}' accounts for {s.percentage_of_total:.1f}% of total {s.metric_name}.",
                    metric=s.metric_name,
                    evidence_data={"segment_value": s.segment_value, "percentage": s.percentage_of_total},
                    calculation_method="Percentage of Total by Dimension",
                    severity="MEDIUM",
                    confidence=1.0,
                    affected_dimensions=[s.dimension]
                ))
                 
        # 3. Variance Insights
        for v in variances:
            if abs(v.percentage_variance) > 10.0:
                direction = "increased" if v.percentage_variance > 0 else "decreased"
                insights.append(InsightObject(
                    run_id=run_id,
                    title=f"Significant {direction.title()} in {v.metric_name}",
                    description=f"{v.metric_name} has {direction} by {abs(v.percentage_variance):.1f}% compared to the previous period.",
                    metric=v.metric_name,
                    evidence_data={"current": v.current_period_value, "previous": v.previous_period_value, "pct_change": v.percentage_variance},
                    calculation_method="Period-over-Period Variance",
                    severity="HIGH" if v.percentage_variance < 0 else "LOW",
                    confidence=1.0
                ))
                
        # 4. Correlation Insights
        for c in correlations:
            if abs(c.correlation_coefficient) > 0.7:
                 strength = "strong positive" if c.correlation_coefficient > 0 else "strong negative"
                 insights.append(InsightObject(
                    run_id=run_id,
                    title=f"Correlation between {c.column_x} and {c.column_y}",
                    description=f"Found a {strength} correlation between {c.column_x} and {c.column_y}.",
                    metric=c.column_x,
                    evidence_data={"r_value": c.correlation_coefficient},
                    calculation_method="Pearson Correlation",
                    severity="LOW",
                    confidence=0.95
                ))

        return insights
