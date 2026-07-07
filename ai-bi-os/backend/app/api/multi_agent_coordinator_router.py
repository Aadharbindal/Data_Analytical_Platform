from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.multi_agent_coordinator import (
    RegisterAgentRequest,
    AgentResponse,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse
)
from app.services.multi_agent_coordinator.coordinator_service import MultiAgentCoordinatorService
from app.services.multi_agent_coordinator.agent_registry_service import AgentRegistryService

router = APIRouter(prefix="/multi-agent", tags=["multi-agent-coordinator"])

@router.post("/agents/register", response_model=AgentResponse)
def register_agent(request: RegisterAgentRequest, db: Session = Depends(get_db)):
    service = AgentRegistryService(db)
    try:
        return service.register_agent(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents", response_model=List[AgentResponse])
def get_agents(db: Session = Depends(get_db)):
    service = AgentRegistryService(db)
    return service.list_agents()

@router.get("/agents/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    service = AgentRegistryService(db)
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/workflow/execute", response_model=WorkflowExecutionResponse)
def execute_workflow(request: WorkflowExecuteRequest, db: Session = Depends(get_db)):
    service = MultiAgentCoordinatorService(db)
    try:
        return service.execute_workflow(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/history", response_model=WorkflowListResponse)
def get_workflow_history(db: Session = Depends(get_db)):
    service = MultiAgentCoordinatorService(db)
    wfs = service.list_workflows()
    return WorkflowListResponse(workflows=wfs, total=len(wfs))

@router.get("/workflow/{workflow_id}", response_model=WorkflowExecutionResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    service = MultiAgentCoordinatorService(db)
    wf = service.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf
