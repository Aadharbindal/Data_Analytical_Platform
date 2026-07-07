from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.schemas.evidence import (
    EvidenceBuildRequest, EvidenceObjectCreate, EvidenceObjectResponse, 
    EvidenceValidationRequest, EvidencePayload
)
from app.repositories.evidence_repository import EvidenceRepository
from .evidence_planner import EvidencePlanner
from .evidence_extractor import EvidenceExtractor
from .evidence_builder import EvidenceBuilder
from .evidence_ranker import EvidenceRanker
from .evidence_validator import EvidenceValidator
from .evidence_policy_engine import EvidencePolicyEngine
from .evidence_cache import evidence_cache
from .evidence_version_manager import EvidenceVersionManager

class EvidenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EvidenceRepository(db)
        self.planner = EvidencePlanner()
        self.extractor = EvidenceExtractor(db)
        self.builder = EvidenceBuilder()
        self.ranker = EvidenceRanker()
        self.validator = EvidenceValidator()
        self.policy_engine = EvidencePolicyEngine()
        self.version_manager = EvidenceVersionManager(db)

    def build_evidence(self, request: EvidenceBuildRequest) -> EvidenceObjectResponse:
        # 1. Plan
        plan = self.planner.plan_extraction(request)
        
        # 2. Extract
        context_obj, extracted_data = self.extractor.extract_from_context(request.context_id)
        
        # 3. Build Raw Evidence
        payload = self.builder.build_evidence_payload(extracted_data, plan)
        
        # 4. Filter Policies
        payload = self.policy_engine.filter_evidence_payload(payload)
        
        # 5. Rank & Score
        payload_size = len(payload.supporting_metrics) + len(payload.supporting_statistics) + len(payload.supporting_objects)
        scores = self.ranker.calculate_scores(payload_size, plan)
        
        # 6. References
        references = self.builder.map_references(request.context_id)
        
        # 7. Create DB Schema
        create_schema = EvidenceObjectCreate(
            workspace_id=request.workspace_id,
            dataset_id=request.dataset_id,
            context_id=request.context_id,
            evidence_type="StatisticalEvidence" if plan.get("extract_statistical") else "KPIEvidence",
            evidence_category="Deterministic",
            evidence_confidence=scores.quality_score or 0.8,
            business_confidence=scores.business_relevance or 0.7,
            validation_status="PENDING",
            payload=payload,
            references=references,
            scores=scores
        )
        
        db_obj = self.repo.create(create_schema)
        response_obj = EvidenceObjectResponse.model_validate(db_obj)
        
        # 8. Validate against hard thresholds
        if self.validator.validate(response_obj):
            db_obj.validation_status = "VALIDATED"
            self.db.commit()
            self.db.refresh(db_obj)
            response_obj = EvidenceObjectResponse.model_validate(db_obj)
        else:
            db_obj.validation_status = "REJECTED"
            self.db.commit()
            self.db.refresh(db_obj)
            response_obj = EvidenceObjectResponse.model_validate(db_obj)
            
        # 9. Cache
        if response_obj.validation_status == "VALIDATED":
            evidence_cache.set_evidence(response_obj)
            
        return response_obj

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceObjectResponse]:
        cached = evidence_cache.get_evidence(evidence_id)
        if cached:
            return cached
            
        db_obj = self.repo.get_by_id(evidence_id)
        if db_obj:
            response_obj = EvidenceObjectResponse.model_validate(db_obj)
            evidence_cache.set_evidence(response_obj)
            return response_obj
        return None

    def validate_evidence(self, request: EvidenceValidationRequest) -> Dict[str, Any]:
        obj = self.get_evidence(request.evidence_id)
        if not obj:
            return {"is_valid": False, "reason": "Not found"}
        is_valid = self.validator.validate(obj)
        return {"is_valid": is_valid, "validation_status": obj.validation_status}

    def get_history(self) -> List[Dict[str, Any]]:
        history = self.repo.get_history()
        return [{"id": h.id, "action": h.action, "timestamp": h.timestamp} for h in history]

    def get_conflicts(self) -> List[Dict[str, Any]]:
        conflicts = self.repo.get_conflicts()
        return [{"id": c.id, "description": c.conflict_description} for c in conflicts]
