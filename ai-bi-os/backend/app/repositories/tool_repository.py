from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime

from app.models.tools import (
    ToolRegistry, ToolDefinition, ToolExecution,
    ToolExecutionHistory, ToolPermission, ToolParameter,
    ToolAudit, ToolMetrics
)
from app.schemas.tools import ToolRegistrationRequest

class ToolRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_registry(self, workspace_id: str, name: str = "default") -> ToolRegistry:
        registry = self.db.query(ToolRegistry).filter(
            ToolRegistry.workspace_id == workspace_id,
            ToolRegistry.name == name
        ).first()
        
        if not registry:
            registry = ToolRegistry(workspace_id=workspace_id, name=name)
            self.db.add(registry)
            self.db.commit()
            self.db.refresh(registry)
            
        return registry

    def register_tool(self, obj_in: ToolRegistrationRequest) -> ToolDefinition:
        registry = self.get_or_create_registry(obj_in.workspace_id)
        
        # Check if exists
        tool = self.db.query(ToolDefinition).filter(
            ToolDefinition.tool_id_string == obj_in.tool_id_string
        ).first()
        
        if not tool:
            tool = ToolDefinition(
                registry_id=registry.id,
                tool_id_string=obj_in.tool_id_string,
                name=obj_in.name,
                description=obj_in.description,
                category=obj_in.category,
                version=obj_in.version,
                input_schema=obj_in.input_schema,
                output_schema=obj_in.output_schema,
                timeout_ms=obj_in.timeout_ms,
                retry_policy=obj_in.retry_policy
            )
            self.db.add(tool)
            self.db.flush()
            
            for p_in in obj_in.permissions:
                self.db.add(ToolPermission(
                    tool_id=tool.id,
                    role_required=p_in.role_required,
                    clearance_level=p_in.clearance_level
                ))
                
            for param_in in obj_in.parameters:
                self.db.add(ToolParameter(
                    tool_id=tool.id,
                    parameter_name=param_in.parameter_name,
                    validation_rules=param_in.validation_rules
                ))
                
            self.db.commit()
            self.db.refresh(tool)
        
        return tool

    def get_tool_by_id_string(self, tool_id_string: str) -> Optional[ToolDefinition]:
        return self.db.query(ToolDefinition).options(
            joinedload(ToolDefinition.permissions),
            joinedload(ToolDefinition.parameters)
        ).filter(ToolDefinition.tool_id_string == tool_id_string).first()

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self.db.query(ToolDefinition).filter(ToolDefinition.id == tool_id).first()

    def get_all_tools(self) -> List[ToolDefinition]:
        return self.db.query(ToolDefinition).filter(ToolDefinition.status == "ACTIVE").all()

    def create_execution(self, tool_id: str, workflow_id: Optional[str], input_parameters: Dict[str, Any], actor_id: str) -> ToolExecution:
        execution = ToolExecution(
            tool_id=tool_id,
            workflow_id=workflow_id,
            input_parameters=input_parameters
        )
        self.db.add(execution)
        self.db.flush()
        
        audit = ToolAudit(
            execution_id=execution.id,
            actor_id=actor_id
        )
        self.db.add(audit)
        
        history = ToolExecutionHistory(
            execution_id=execution.id,
            status_to="PENDING"
        )
        self.db.add(history)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_execution(self, execution_id: str, status: str, output: Dict[str, Any] = None, error_details: str = None, latency_ms: int = None):
        execution = self.db.query(ToolExecution).filter(ToolExecution.id == execution_id).first()
        if not execution:
            return
            
        old_status = execution.status
        execution.status = status
        
        if output:
            execution.output = output
        if error_details:
            execution.error_details = error_details
            
        if status in ["COMPLETED", "FAILED", "TIMEOUT"]:
            execution.completed_at = datetime.utcnow()
            
            # Metrics
            is_success = status == "COMPLETED"
            metrics = ToolMetrics(
                execution_id=execution.id,
                latency_ms=latency_ms,
                is_success=is_success
            )
            self.db.add(metrics)
            
        self.db.add(execution)
        
        history = ToolExecutionHistory(
            execution_id=execution.id,
            status_from=old_status,
            status_to=status
        )
        self.db.add(history)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_execution(self, execution_id: str) -> Optional[ToolExecution]:
        return self.db.query(ToolExecution).filter(ToolExecution.id == execution_id).first()

    def get_history(self) -> List[ToolExecution]:
        return self.db.query(ToolExecution).order_by(desc(ToolExecution.started_at)).limit(100).all()
