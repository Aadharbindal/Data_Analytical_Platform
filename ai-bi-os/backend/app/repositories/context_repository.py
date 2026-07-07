from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.context import (
    ContextObject, ContextVersion, ContextMetadata, 
    ContextReference, ContextDependency, ContextPolicy, 
    ContextHistory, ContextCache
)
from app.schemas.context_builder import ContextObjectCreate

class ContextRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, context_id: str) -> Optional[ContextObject]:
        return self.db.query(ContextObject).options(
            joinedload(ContextObject.references),
            joinedload(ContextObject.versions),
            joinedload(ContextObject.metadata_info)
        ).filter(ContextObject.id == context_id).first()

    def get_by_conversation(self, conversation_id: str) -> List[ContextObject]:
        return self.db.query(ContextObject).filter(
            ContextObject.conversation_id == conversation_id
        ).order_by(desc(ContextObject.generated_timestamp)).all()

    def get_by_dataset(self, dataset_id: str) -> List[ContextObject]:
        return self.db.query(ContextObject).filter(
            ContextObject.dataset_id == dataset_id
        ).order_by(desc(ContextObject.generated_timestamp)).all()

    def create(self, obj_in: ContextObjectCreate, analytics_refs: List[Dict[str, Any]] = None) -> ContextObject:
        db_obj = ContextObject(
            workspace_id=obj_in.workspace_id,
            dataset_id=obj_in.dataset_id,
            dataset_version=obj_in.dataset_version,
            conversation_id=obj_in.conversation_id,
            request_id=obj_in.request_id,
            context_purpose=obj_in.context_purpose,
            business_domain=obj_in.business_domain,
            context_payload=obj_in.context_payload.model_dump()
        )
        self.db.add(db_obj)
        self.db.flush()

        # Add references to Analytics Objects
        if analytics_refs:
            for ref in analytics_refs:
                db_ref = ContextReference(
                    context_id=db_obj.id,
                    analytics_object_id=ref.get('id'),
                    relevance_score=ref.get('relevance_score', 1.0)
                )
                self.db.add(db_ref)

        # Create Initial Version
        version = ContextVersion(
            context_id=db_obj.id,
            version_number=1,
            snapshot=db_obj.context_payload
        )
        self.db.add(version)

        # Log History
        history = ContextHistory(
            context_id=db_obj.id,
            action="BUILT",
            actor="SYSTEM",
            details={"message": "Context object constructed"}
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def rebuild(self, context_id: str, new_payload: Dict[str, Any]) -> Optional[ContextObject]:
        db_obj = self.get_by_id(context_id)
        if not db_obj:
            return None
            
        db_obj.context_payload = new_payload
        
        # New Version
        latest_version = self.db.query(ContextVersion).filter(
            ContextVersion.context_id == context_id
        ).order_by(desc(ContextVersion.version_number)).first()
        
        new_version_num = latest_version.version_number + 1 if latest_version else 2
        
        version = ContextVersion(
            context_id=db_obj.id,
            version_number=new_version_num,
            snapshot=new_payload
        )
        self.db.add(version)
        
        history = ContextHistory(
            context_id=db_obj.id,
            action="REBUILT",
            actor="SYSTEM",
            details={"version": new_version_num}
        )
        self.db.add(history)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_history(self, context_id: Optional[str] = None) -> List[ContextHistory]:
        query = self.db.query(ContextHistory)
        if context_id:
            query = query.filter(ContextHistory.context_id == context_id)
        return query.order_by(desc(ContextHistory.timestamp)).limit(100).all()
