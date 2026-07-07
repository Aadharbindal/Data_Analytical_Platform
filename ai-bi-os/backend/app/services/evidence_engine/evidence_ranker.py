from app.schemas.evidence import EvidenceScoreBase

class EvidenceRanker:
    def __init__(self):
        pass

    def calculate_scores(self, payload_size: int, plan: dict) -> EvidenceScoreBase:
        # Example logic to deterministically score evidence based on completeness/type
        quality = 0.9 if plan.get("extract_statistical") else 0.7
        business = 0.85 if plan.get("extract_kpi") else 0.5
        
        return EvidenceScoreBase(
            quality_score=quality,
            freshness_score=1.0,
            reliability_score=0.95,
            completeness_score=min(1.0, payload_size / 10),
            consistency_score=1.0,
            business_relevance=business
        )
