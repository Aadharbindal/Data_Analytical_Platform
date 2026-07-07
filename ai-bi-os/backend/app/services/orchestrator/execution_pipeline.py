from typing import Dict, Any
from app.repositories.orchestrator_repository import OrchestratorRepository
from .intent_router import IntentRouter
from .workflow_planner import WorkflowPlanner
from .agent_router import AgentRouter
from .model_resolver import ModelResolver
from .context_resolver import ContextResolver
from .evidence_resolver import EvidenceResolver
from .prompt_resolver import PromptResolver
from .response_aggregator import ResponseAggregator
from .execution_validator import ExecutionValidator

class ExecutionPipeline:
    def __init__(self, repo: OrchestratorRepository):
        self.repo = repo
        self.intent_router = IntentRouter()
        self.workflow_planner = WorkflowPlanner()
        self.agent_router = AgentRouter()
        self.model_resolver = ModelResolver()
        self.context_resolver = ContextResolver()
        self.evidence_resolver = EvidenceResolver()
        self.prompt_resolver = PromptResolver()
        self.aggregator = ResponseAggregator()
        self.validator = ExecutionValidator()

    def run_pipeline(self, execution_id: str) -> bool:
        """
        Synchronously runs the state machine.
        In a distributed setup, this would be a directed graph in Celery/LangGraph.
        """
        execution = self.repo.get_execution(execution_id)
        if not execution:
            return False

        try:
            self.repo.update_execution_status(execution_id, "PLANNING")
            
            # Step 1: Intent
            intent_res = self.intent_router.classify_intent(execution.user_request)
            self.repo.update_execution_intent(execution_id, intent_res.intent, intent_res.confidence)
            
            # Step 2: Plan
            plan = self.workflow_planner.build_plan(intent_res.intent, execution.workspace_id)
            self.repo.save_plan(execution_id, plan.model_dump())
            
            self.repo.update_execution_status(execution_id, "ROUTING")
            
            # Step 3: Agents & Models
            selected_agent = self.agent_router.select_agent(intent_res.intent)
            selected_model = self.model_resolver.select_model(intent_res.intent)
            
            # In a real DB we'd update the execution row here
            
            self.repo.update_execution_status(execution_id, "EXECUTING")
            
            # Step 4: Resolve dependencies
            ctx_id = self.context_resolver.resolve_context(plan.model_dump())
            evd_id = self.evidence_resolver.resolve_evidence(ctx_id, plan.model_dump())
            prm_id = self.prompt_resolver.resolve_prompt(ctx_id, evd_id, intent_res.intent, execution.user_request)
            
            # Step 5: Fake Execution (We just orchestrate, we don't generate)
            mock_results = [{"content": f"Result from {selected_agent} using {selected_model.model_name}"}]
            
            # Step 6: Validation
            self.repo.update_execution_status(execution_id, "VALIDATING")
            final_output = self.aggregator.aggregate(mock_results)
            is_valid = self.validator.validate(final_output, plan.validation_rules or {})
            
            if is_valid:
                self.repo.update_execution_status(execution_id, "COMPLETED", {"output": final_output})
                return True
            else:
                self.repo.update_execution_status(execution_id, "FAILED", {"error": "Validation failed"})
                return False
                
        except Exception as e:
            self.repo.update_execution_status(execution_id, "FAILED", {"error": str(e)})
            return False
