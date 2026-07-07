import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.insight_generation import (
    InsightGenerationObject, InsightReference, InsightHistory,
    InsightPriority, InsightObjectValidation, InsightMetrics
)
from app.schemas.insight_generation import InsightGenerateRequest
from app.repositories.insight_generation_repository import InsightGenerationRepository

class InsightCache:
    """In-memory cache acting as a fallback for Redis-based insight caching."""
    _cache = {}
    
    @classmethod
    def get(cls, key: str):
        return cls._cache.get(key)
        
    @classmethod
    def set(cls, key: str, value: Any):
        cls._cache[key] = value

class InsightValidator:
    """Validates inputs before generation, ensuring no hallucinations by requiring evidence."""
    def validate(self, request: InsightGenerateRequest) -> bool:
        if not request.evidence_references:
            raise ValueError("Cannot generate insight: No evidence references provided. The engine must NEVER hallucinate.")
        return True

class InsightPrioritizer:
    """Heuristic based prioritizer to score insights by business impact."""
    def calculate_priority(self, domain: str, confidence: float) -> tuple[float, int, str]:
        # Mock heuristic logic
        base_impact = 50.0
        if domain.lower() in ["revenue", "sales", "finance"]:
            base_impact += 30.0
            
        impact = base_impact * confidence
        
        priority = 5
        severity = "LOW"
        
        if impact > 75:
            priority = 1
            severity = "HIGH"
        elif impact > 50:
            priority = 3
            severity = "MEDIUM"
            
        return impact, priority, severity

class NarrativeGenerator:
    """Abstracted layer for orchestrator call to generate the human-readable text."""
    def generate(self, request: InsightGenerateRequest) -> tuple[str, str, float]:
        # In a real scenario, this delegates to the Orchestrator Engine (Module 36).
        # We mock the reasoning here.
        headline = f"Key {request.insight_type} detected in {request.business_domain}"
        narrative = f"What happened: Analytics indicates a significant pattern in {request.business_domain}.\n\n" \
                    f"Why it happened: Contributing factors derived from evidence objects show strong correlation.\n\n" \
                    f"Business impact: This could affect overall metrics by up to 15%.\n\n" \
                    f"Limitations: Confidence is bound by the quality of the dataset."
        confidence = 0.92
        return headline, narrative, confidence

class InsightManager:
    """High-level orchestrator service."""
    def __init__(self, db: Session):
        self.db = db
        self.repository = InsightGenerationRepository(db)
        self.validator = InsightValidator()
        self.prioritizer = InsightPrioritizer()
        self.narrative_generator = NarrativeGenerator()

    def generate_insight(self, request: InsightGenerateRequest) -> InsightGenerationObject:
        start_time = time.time()
        
        # 1. Validate
        self.validator.validate(request)
        
        # 2. Generate Narrative
        headline, narrative, confidence = self.narrative_generator.generate(request)
        
        # 3. Prioritize
        impact, priority, severity = self.prioritizer.calculate_priority(request.business_domain, confidence)
        
        # 4. Save Core Object
        insight = InsightGenerationObject(
            workspace_id=request.workspace_id,
            dataset_id=request.dataset_id,
            conversation_id=request.conversation_id,
            insight_type=request.insight_type,
            business_domain=request.business_domain,
            headline=headline,
            detailed_narrative=narrative,
            confidence_score=confidence,
            business_impact_score=impact,
            priority=priority,
            severity=severity
        )
        created = self.repository.create_insight(insight)
        
        # 5. Save References
        for ref in request.evidence_references:
            self.repository.add_reference(InsightReference(insight_id=created.id, reference_type="EVIDENCE", reference_id=ref.reference_id))
            
        for ref in request.context_references:
            self.repository.add_reference(InsightReference(insight_id=created.id, reference_type="CONTEXT", reference_id=ref.reference_id))
            
        # 6. Save History & Validation
        self.repository.add_history(InsightHistory(insight_id=created.id, action="GENERATED"))
        self.repository.add_validation(InsightObjectValidation(insight_id=created.id, is_valid=True, validation_notes="Evidence checks passed."))
        
        # 7. Metrics
        latency = int((time.time() - start_time) * 1000)
        self.repository.log_metrics(InsightMetrics(
            workspace_id=request.workspace_id,
            generation_time_ms=latency,
            confidence=confidence,
            business_impact=impact,
            passed_validation=True
        ))
        
        return created

    def get_insight(self, insight_id: str) -> Optional[InsightGenerationObject]:
        return self.repository.get_insight(insight_id)
        
    def list_by_workspace(self, workspace_id: str) -> List[InsightGenerationObject]:
        return self.repository.list_insights_by_workspace(workspace_id)
        
    def get_summary(self, workspace_id: str) -> Dict[str, Any]:
        insights = self.repository.list_insights_by_workspace(workspace_id, limit=1000)
        total = len(insights)
        avg_conf = sum(i.confidence_score for i in insights) / total if total > 0 else 0
        avg_impact = sum(i.business_impact_score for i in insights) / total if total > 0 else 0
        domains = list(set([i.business_domain for i in insights]))
        
        return {
            "total_insights": total,
            "avg_confidence": avg_conf,
            "avg_business_impact": avg_impact,
            "top_domains": domains[:5]
        }
