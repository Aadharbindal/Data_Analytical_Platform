from typing import List, Dict, Any
from app.models.insight import Insight, InsightEvidence, InsightScore

class InsightGenerator:
    """The core engine containing deterministic logic for Patterns, Contributions, Changes, Anomalies, Risks, Opportunities, and Root Causes."""
    
    @staticmethod
    def generate(plan: Dict[str, Any]) -> List[Insight]:
        insights = []
        dataset_version_id = plan["dataset_version_id"]
        data = plan["data"]
        
        # 1. Change Detection / Variance Insights
        if plan["has_variances"]:
            for v in data["variances"]:
                if abs(v.percentage_variance) > 15.0:
                    insight_type = "SUDDEN_GROWTH" if v.percentage_variance > 0 else "SUDDEN_DECLINE"
                    category = "OPPORTUNITY" if v.percentage_variance > 0 else "RISK"
                    
                    insight = Insight(
                        dataset_version_id=dataset_version_id,
                        title=f"{insight_type.replace('_', ' ').title()} in {v.metric_name}",
                        category=category,
                        insight_type=insight_type,
                        metric=v.metric_name,
                        severity="HIGH" if abs(v.percentage_variance) > 30 else "MEDIUM"
                    )
                    
                    evidence = InsightEvidence(
                        evidence_type="VARIANCE_ID",
                        reference_id=v.id,
                        data={"pct_variance": v.percentage_variance, "absolute_variance": v.absolute_variance}
                    )
                    insight.evidence.append(evidence)
                    
                    score = InsightScore(
                        confidence=0.95,
                        business_impact=0.8 if abs(v.percentage_variance) > 30 else 0.5,
                        urgency=0.9 if category == "RISK" else 0.4,
                        novelty=0.7
                    )
                    insight.score = score
                    insights.append(insight)
                    
        # 2. Pattern Detection / Trend Insights
        if plan["has_trends"]:
            for t in data["trends"]:
                if t.slope and t.slope > 1.2:
                    insight = Insight(
                        dataset_version_id=dataset_version_id,
                        title=f"Strong Upward Trend in {t.metric_name}",
                        category="TREND",
                        insight_type="RECURRING_GROWTH",
                        metric=t.metric_name,
                        severity="LOW"
                    )
                    evidence = InsightEvidence(
                        evidence_type="TREND_ID",
                        reference_id=t.id,
                        data={"slope": t.slope, "confidence": t.confidence}
                    )
                    insight.evidence.append(evidence)
                    
                    score = InsightScore(
                        confidence=t.confidence or 0.8,
                        business_impact=0.6,
                        urgency=0.2,
                        novelty=0.5
                    )
                    insight.score = score
                    insights.append(insight)

        # 3. Root Cause / Contribution Insights
        if plan["has_segments"] and plan["has_variances"]:
            # Deterministic Root Cause logic: If variance is negative, find the segment with highest concentration
            # In a real engine, we'd calculate variance *per segment*. Here we use concentration as a proxy.
            negative_variances = [v for v in data["variances"] if v.percentage_variance < 0]
            if negative_variances:
                v = negative_variances[0]
                # Find corresponding segments for this metric
                relevant_segments = [s for s in data["segments"] if s.metric_name == v.metric_name]
                if relevant_segments:
                    # Sort by percentage of total descending
                    relevant_segments.sort(key=lambda x: x.percentage_of_total or 0, reverse=True)
                    top_segment = relevant_segments[0]
                    
                    if top_segment.percentage_of_total and top_segment.percentage_of_total > 30.0:
                        insight = Insight(
                            dataset_version_id=dataset_version_id,
                            title=f"Root Cause for {v.metric_name} Decline",
                            category="ROOT_CAUSE",
                            insight_type="LOSS_DRIVER",
                            metric=v.metric_name,
                            affected_entities=[f"{top_segment.dimension}: {top_segment.segment_value}"],
                            severity="HIGH"
                        )
                        
                        evidence = InsightEvidence(
                            evidence_type="SEGMENT_ID",
                            reference_id=top_segment.id,
                            data={"segment": top_segment.segment_value, "concentration": top_segment.percentage_of_total}
                        )
                        insight.evidence.append(evidence)
                        
                        score = InsightScore(
                            confidence=0.85,
                            business_impact=0.9,
                            urgency=0.95,
                            novelty=0.8
                        )
                        insight.score = score
                        insights.append(insight)

        # 4. Forecast Governance / Model Health Insights
        if plan.get("has_governance") and "governance" in data:
            govs = data["governance"]
            for g in govs:
                if g.quality_score is not None and g.quality_score < 80.0:
                    insight = Insight(
                        dataset_version_id=dataset_version_id,
                        title=f"Forecast Model Quality Degradation: {g.name}",
                        category="RISK",
                        insight_type="MODEL_DRIFT",
                        metric="quality_score",
                        affected_entities=[g.model_id],
                        severity="HIGH"
                    )
                    
                    evidence = InsightEvidence(
                        evidence_type="GOVERNANCE_ID",
                        reference_id=g.id,
                        data={"quality_score": g.quality_score, "trust_score": g.trust_score}
                    )
                    insight.evidence.append(evidence)
                    
                    score = InsightScore(
                        confidence=0.99,
                        business_impact=0.9,
                        urgency=0.95,
                        novelty=0.1
                    )
                    insight.score = score
                    insights.append(insight)

        return insights
