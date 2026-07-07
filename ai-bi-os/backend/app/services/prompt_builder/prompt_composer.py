from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.schemas.prompt import PromptSectionBase, PromptPayload
from app.services.context_builder import ContextBuilderService
from app.services.evidence_engine import EvidenceService

class PromptComposer:
    def __init__(self, db: Session):
        self.context_service = ContextBuilderService(db)
        self.evidence_service = EvidenceService(db)

    def fetch_dependencies(self, context_id: str, evidence_id: str) -> tuple:
        ctx = self.context_service.get_context(context_id)
        evd = self.evidence_service.get_evidence(evidence_id)
        if not ctx:
            raise ValueError(f"Context Object {context_id} missing")
        if not evd:
            raise ValueError(f"Evidence Object {evidence_id} missing")
        return ctx, evd

    def compose(self, plan: dict, ctx, evd, req: str) -> tuple[PromptPayload, List[PromptSectionBase]]:
        payload = PromptPayload()
        sections = []
        
        if plan.get("include_system"):
            val = "You are an Enterprise AI Agent. Respond strictly using the provided Evidence."
            payload.system_instructions = val
            sections.append(PromptSectionBase(section_name="System", content=val, section_priority=10))
            
        if plan.get("include_evidence"):
            val = str(evd.payload.model_dump())
            payload.evidence_context = val
            sections.append(PromptSectionBase(section_name="Evidence", content=val, section_priority=9))
            
        if plan.get("include_constraints"):
            val = "Do not hallucinate. Do not provide information outside of the Evidence block."
            payload.constraints = val
            sections.append(PromptSectionBase(section_name="Constraints", content=val, section_priority=8))
            
        if req:
            payload.user_request = req
            sections.append(PromptSectionBase(section_name="UserRequest", content=req, section_priority=7))

        return payload, sections
