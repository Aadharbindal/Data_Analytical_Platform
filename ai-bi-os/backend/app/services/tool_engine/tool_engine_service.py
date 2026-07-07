from sqlalchemy.orm import Session
from typing import List, Dict, Any
import time

from app.repositories.tool_repository import ToolRepository
from app.schemas.tools import (
    ToolRegistrationRequest, ToolResponse,
    ToolExecutionRequest, ToolExecutionResponse,
    ToolValidationRequest
)

from .tool_registry_service import ToolRegistryService
from .tool_discovery_service import ToolDiscoveryService
from .tool_validator import ToolValidator
from .parameter_validator import ParameterValidator
from .permission_manager import PermissionManager
from .tool_executor import ToolExecutor
from .execution_monitor import ExecutionMonitor
from .response_normalizer import ResponseNormalizer
from .tool_cache import tool_cache

class ToolEngineService:
    def __init__(self, db: Session):
        self.repo = ToolRepository(db)
        
        self.registry = ToolRegistryService(self.repo)
        self.discovery = ToolDiscoveryService(self.repo)
        
        self.tool_validator = ToolValidator(self.repo)
        self.param_validator = ParameterValidator()
        self.perm_manager = PermissionManager()
        
        self.executor = ToolExecutor()
        self.monitor = ExecutionMonitor()
        self.normalizer = ResponseNormalizer()

    def register_tool(self, request: ToolRegistrationRequest) -> ToolResponse:
        tool_cache.invalidate(request.tool_id_string)
        return self.registry.register_tool(request)

    def get_tool(self, tool_id: str) -> ToolResponse:
        return self.registry.get_tool(tool_id)

    def get_all_tools(self) -> List[ToolResponse]:
        return self.discovery.get_all_tools()

    def validate_tool_call(self, request: ToolValidationRequest) -> bool:
        """
        Dry-run validation without execution.
        """
        tool = self.tool_validator.validate_tool_exists(request.tool_id_string)
        self.perm_manager.check_permissions(tool, request.actor_id)
        self.param_validator.validate_parameters(tool, request.input_parameters)
        return True

    def execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResponse:
        """
        Validates, executes, and normalizes the tool invocation.
        """
        start_time = time.time()
        
        tool = self.tool_validator.validate_tool_exists(request.tool_id_string)
        
        execution = self.repo.create_execution(
            tool_id=tool.id,
            workflow_id=request.workflow_id,
            input_parameters=request.input_parameters,
            actor_id=request.actor_id
        )
        
        try:
            # Pre-execution checks
            self.perm_manager.check_permissions(tool, request.actor_id)
            self.param_validator.validate_parameters(tool, request.input_parameters)
            
            # Execute
            self.repo.update_execution(execution.id, status="EXECUTING")
            
            output = self.executor.execute_tool_sync(request.tool_id_string, request.input_parameters)
            
            latency = int((time.time() - start_time) * 1000)
            
            updated_exec = self.repo.update_execution(
                execution.id,
                status="COMPLETED",
                output=output,
                latency_ms=latency
            )
            return self.normalizer.normalize(updated_exec)
            
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            updated_exec = self.repo.update_execution(
                execution.id,
                status="FAILED",
                error_details=str(e),
                latency_ms=latency
            )
            return self.normalizer.normalize(updated_exec)

    def get_executions(self) -> List[ToolExecutionResponse]:
        executions = self.repo.get_history()
        return [self.normalizer.normalize(ex) for ex in executions]

    def cancel_execution(self, execution_id: str) -> ToolExecutionResponse:
        updated = self.repo.update_execution(execution_id, status="FAILED", error_details="Cancelled by user")
        return self.normalizer.normalize(updated)
