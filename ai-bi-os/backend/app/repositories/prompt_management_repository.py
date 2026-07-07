from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.prompt_management import (
    PromptRegistry, PromptTemplate, PromptVersion,
    PromptLifecycle, PromptApproval, PromptReview,
    PromptDiff, PromptManagementAudit
)
from app.schemas.prompt_management import PromptTemplateCreate, PromptVersionCreate

class PromptManagementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_registry(self, workspace_id: str, name: str, prompt_type: str) -> PromptRegistry:
        registry = self.db.query(PromptRegistry).filter(
            PromptRegistry.workspace_id == workspace_id,
            PromptRegistry.name == name
        ).first()
        
        if not registry:
            registry = PromptRegistry(workspace_id=workspace_id, name=name, prompt_type=prompt_type)
            self.db.add(registry)
            self.db.commit()
            self.db.refresh(registry)
            
        return registry

    def create_template(self, obj_in: PromptTemplateCreate) -> PromptTemplate:
        registry = self.get_or_create_registry(obj_in.workspace_id, obj_in.name, obj_in.prompt_type)
        
        template = PromptTemplate(
            registry_id=registry.id,
            template_structure=obj_in.template_structure,
            variables=obj_in.variables
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        return self.db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    def get_templates_by_workspace(self, workspace_id: str) -> List[PromptTemplate]:
        return self.db.query(PromptTemplate).join(PromptRegistry).filter(
            PromptRegistry.workspace_id == workspace_id
        ).all()

    def get_version(self, version_id: str) -> Optional[PromptVersion]:
        return self.db.query(PromptVersion).options(
            joinedload(PromptVersion.lifecycle)
        ).filter(PromptVersion.id == version_id).first()

    def get_latest_version(self, template_id: str) -> Optional[PromptVersion]:
        return self.db.query(PromptVersion).filter(
            PromptVersion.template_id == template_id
        ).order_by(desc(PromptVersion.created_at)).first()

    def create_version(self, obj_in: PromptVersionCreate, version_string: str) -> PromptVersion:
        version = PromptVersion(
            template_id=obj_in.template_id,
            parent_version_id=obj_in.parent_version_id,
            version_string=version_string,
            is_major=obj_in.is_major,
            content=obj_in.content,
            estimated_tokens=obj_in.estimated_tokens,
            author_id=obj_in.author_id
        )
        self.db.add(version)
        self.db.flush()
        
        lifecycle = PromptLifecycle(
            version_id=version.id,
            status="DRAFT"
        )
        self.db.add(lifecycle)
        
        self.log_audit(version.id, obj_in.author_id, "CREATED", {"version": version_string})
        
        self.db.commit()
        self.db.refresh(version)
        return version

    def update_lifecycle_status(self, version_id: str, status: str, actor_id: str, rollback_ref: Optional[str] = None):
        lifecycle = self.db.query(PromptLifecycle).filter(PromptLifecycle.version_id == version_id).first()
        if lifecycle:
            lifecycle.status = status
            if rollback_ref:
                lifecycle.rollback_reference = rollback_ref
            self.db.add(lifecycle)
            self.log_audit(version_id, actor_id, status, {"rollback_ref": rollback_ref})
            self.db.commit()

    def create_review(self, version_id: str, reviewer_id: str, comments: Optional[str]):
        approval = self.db.query(PromptApproval).filter(
            PromptApproval.version_id == version_id,
            PromptApproval.status == "PENDING"
        ).first()
        
        if not approval:
            approval = PromptApproval(version_id=version_id, status="PENDING")
            self.db.add(approval)
            self.db.flush()
            
        review = PromptReview(
            approval_id=approval.id,
            reviewer_id=reviewer_id,
            comments=comments
        )
        self.db.add(review)
        self.update_lifecycle_status(version_id, "REVIEW", reviewer_id)
        self.db.commit()

    def approve_version(self, version_id: str, approver_id: str):
        approval = self.db.query(PromptApproval).filter(
            PromptApproval.version_id == version_id,
            PromptApproval.status == "PENDING"
        ).first()
        
        if approval:
            approval.status = "APPROVED"
            approval.approver_id = approver_id
            self.db.add(approval)
            
        self.update_lifecycle_status(version_id, "APPROVED", approver_id)

    def get_diff(self, version_id: str) -> Optional[PromptDiff]:
        return self.db.query(PromptDiff).filter(PromptDiff.version_id == version_id).first()

    def save_diff(self, diff_obj: PromptDiff):
        self.db.add(diff_obj)
        self.db.commit()

    def log_audit(self, version_id: str, actor_id: str, action: str, details: Dict[str, Any] = None):
        audit = PromptManagementAudit(
            version_id=version_id,
            actor_id=actor_id,
            action=action,
            details=details
        )
        self.db.add(audit)

    def get_history(self) -> List[PromptManagementAudit]:
        return self.db.query(PromptManagementAudit).order_by(desc(PromptManagementAudit.timestamp)).limit(100).all()
