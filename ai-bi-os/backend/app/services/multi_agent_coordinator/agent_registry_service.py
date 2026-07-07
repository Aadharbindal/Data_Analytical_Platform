from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.multi_agent_coordinator import AgentDefinition
from app.repositories.multi_agent_coordinator_repository import MultiAgentCoordinatorRepository
from app.schemas.multi_agent_coordinator import RegisterAgentRequest

class AgentRegistryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MultiAgentCoordinatorRepository(db)

    def register_agent(self, request: RegisterAgentRequest) -> AgentDefinition:
        existing = self.repository.get_agent_by_name(request.name)
        if existing:
            # Upsert
            existing.description = request.description
            existing.version = request.version
            existing.capabilities = request.capabilities
            existing.input_schema = request.input_schema
            existing.output_schema = request.output_schema
            self.db.commit()
            self.db.refresh(existing)
            return existing
            
        new_agent = AgentDefinition(
            workspace_id=request.workspace_id,
            name=request.name,
            description=request.description,
            version=request.version,
            capabilities=request.capabilities,
            input_schema=request.input_schema,
            output_schema=request.output_schema
        )
        return self.repository.create_agent(new_agent)

    def list_agents(self) -> List[AgentDefinition]:
        return self.repository.list_agents()

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self.repository.get_agent(agent_id)
