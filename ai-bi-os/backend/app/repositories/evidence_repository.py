from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.evidence import (
    EvidenceObject, EvidenceMetadata, EvidenceReference, 
    EvidenceScore, EvidenceConflict, EvidenceHistory, EvidencePolicy
)
from app.schemas.evidence import EvidenceObjectCreate

class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceObject]:
        return self.db.query(EvidenceObject).options(
            joinedload(EvidenceObject.references),
            joinedload(EvidenceObject.scores),
            joinedload(EvidenceObject.conflicts)
        ).filter(EvidenceObject.id == evidence_id).first()

    def get_by_context(self, context_id: str) -> List[EvidenceObject]:
        return self.db.query(EvidenceObject).filter(
            EvidenceObject.context_id == context_id
        ).order_by(desc(EvidenceObject.created_timestamp)).all()

    def get_by_dataset(self, dataset_id: str) -> List[EvidenceObject]:
        return self.db.query(EvidenceObject).filter(
            EvidenceObject.dataset_id == dataset_id
        ).order_by(desc(EvidenceObject.created_timestamp)).all()

    def create(self, obj_in: EvidenceObjectCreate) -> EvidenceObject:
        db_obj = EvidenceObject(
            workspace_id=obj_in.workspace_id,
            dataset_id=obj_in.dataset_id,
            dataset_version=obj_in.dataset_version,
            context_id=obj_in.context_id,
            evidence_type=obj_in.evidence_type,
            evidence_category=obj_in.evidence_category,
            evidence_priority=obj_in.evidence_priority,
            evidence_confidence=obj_in.evidence_confidence,
            business_confidence=obj_in.business_confidence,
            validation_status=obj_in.validation_status,
            payload=obj_in.payload.model_dump()
        )
        self.db.add(db_obj)
        self.db.flush()

        # Add references
        for ref in obj_in.references:
            db_ref = EvidenceReference(
                evidence_id=db_obj.id,
                source_type=ref.source_type,
                source_id=ref.source_id
            )
            self.db.add(db_ref)

        # Add Scores
        if obj_in.scores:
            db_score = EvidenceScore(
                evidence_id=db_obj.id,
                quality_score=obj_in.scores.quality_score,
                freshness_score=obj_in.scores.freshness_score,
                reliability_score=obj_in.scores.reliability_score,
                completeness_score=obj_in.scores.completeness_score,
                consistency_score=obj_in.scores.consistency_score,
                business_relevance=obj_in.scores.business_relevance
            )
            self.db.add(db_score)

        # Log History
        history = EvidenceHistory(
            evidence_id=db_obj.id,
            action="BUILT",
            actor="SYSTEM",
            details={"message": "Evidence object constructed"}
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_history(self, evidence_id: Optional[str] = None) -> List[EvidenceHistory]:
        query = self.db.query(EvidenceHistory)
        if evidence_id:
            query = query.filter(EvidenceHistory.evidence_id == evidence_id)
        return query.order_by(desc(EvidenceHistory.timestamp)).limit(100).all()

    def get_conflicts(self, evidence_id: Optional[str] = None) -> List[EvidenceConflict]:
        query = self.db.query(EvidenceConflict).filter(EvidenceConflict.resolved == False)
        if evidence_id:
            query = query.filter(EvidenceConflict.evidence_id == evidence_id)
        return query.all()
