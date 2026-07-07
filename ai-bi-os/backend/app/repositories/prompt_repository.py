from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.prompt import (
    PromptObject, PromptMetadata, PromptSection, 
    PromptReference, PromptValidation, PromptOptimization, 
    PromptHistory, PromptAudit
)
from app.schemas.prompt import PromptObjectCreate

class PromptRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, prompt_id: str) -> Optional[PromptObject]:
        return self.db.query(PromptObject).options(
            joinedload(PromptObject.references),
            joinedload(PromptObject.sections),
            joinedload(PromptObject.optimizations),
            joinedload(PromptObject.validations)
        ).filter(PromptObject.id == prompt_id).first()

    def get_by_conversation(self, conversation_id: str) -> List[PromptObject]:
        return self.db.query(PromptObject).filter(
            PromptObject.conversation_id == conversation_id
        ).order_by(desc(PromptObject.created_timestamp)).all()

    def create(self, obj_in: PromptObjectCreate) -> PromptObject:
        db_obj = PromptObject(
            workspace_id=obj_in.workspace_id,
            conversation_id=obj_in.conversation_id,
            request_id=obj_in.request_id,
            prompt_type=obj_in.prompt_type,
            prompt_version=obj_in.prompt_version,
            prompt_priority=obj_in.prompt_priority,
            prompt_size=obj_in.prompt_size,
            estimated_tokens=obj_in.estimated_tokens,
            validation_status=obj_in.validation_status,
            structured_prompt=obj_in.structured_prompt.model_dump()
        )
        self.db.add(db_obj)
        self.db.flush()

        # Add references
        for ref in obj_in.references:
            db_ref = PromptReference(
                prompt_id=db_obj.id,
                source_type=ref.source_type,
                source_id=ref.source_id
            )
            self.db.add(db_ref)

        # Add Sections
        for sec in obj_in.sections:
            db_sec = PromptSection(
                prompt_id=db_obj.id,
                section_name=sec.section_name,
                content=sec.content,
                section_priority=sec.section_priority
            )
            self.db.add(db_sec)

        # Add Optimizations
        if obj_in.optimizations:
            db_opt = PromptOptimization(
                prompt_id=db_obj.id,
                original_size=obj_in.optimizations.original_size,
                optimized_size=obj_in.optimizations.optimized_size,
                optimization_ratio=obj_in.optimizations.optimization_ratio,
                actions_taken=obj_in.optimizations.actions_taken
            )
            self.db.add(db_opt)

        # Log History
        history = PromptHistory(
            prompt_id=db_obj.id,
            action="BUILT",
            details={"message": "Prompt object constructed"}
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_validation(self, prompt_id: str, is_valid: bool, vtype: str, details: str):
        val = PromptValidation(
            prompt_id=prompt_id,
            is_valid=is_valid,
            validation_type=vtype,
            details=details
        )
        self.db.add(val)
        self.db.commit()

    def get_history(self, prompt_id: Optional[str] = None) -> List[PromptHistory]:
        query = self.db.query(PromptHistory)
        if prompt_id:
            query = query.filter(PromptHistory.prompt_id == prompt_id)
        return query.order_by(desc(PromptHistory.timestamp)).limit(100).all()
