import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.business_rule_engine import (
    RuleDefinition, BusinessRuleEngineVersion, BusinessRuleEngineExecution, RuleMetrics
)
from app.schemas.business_rule_engine import (
    RuleCreateRequest, RuleEvaluateRequest
)
from app.repositories.business_rule_engine_repository import BusinessRuleEngineRepository
from app.services.business_rule_engine.rule_evaluator import RuleEvaluator

class RuleValidator:
    """Validates structural integrity of AST."""
    def validate(self, ast: Dict[str, Any]) -> bool:
        if not ast:
            raise ValueError("Rule expression cannot be empty.")
        if "operator" not in ast:
            raise ValueError("Rule expression must have an operator.")
        return True

class RuleEngineService:
    """High-level orchestrator service."""
    def __init__(self, db: Session):
        self.db = db
        self.repository = BusinessRuleEngineRepository(db)
        self.validator = RuleValidator()
        self.evaluator = RuleEvaluator()

    def create_rule(self, request: RuleCreateRequest) -> RuleDefinition:
        self.validator.validate(request.expression_ast)
        
        rule = RuleDefinition(
            workspace_id=request.workspace_id,
            department=request.department,
            rule_name=request.rule_name,
            rule_category=request.rule_category,
            description=request.description,
            priority=request.priority,
            severity=request.severity,
            expression_ast=request.expression_ast,
            action=request.action,
            author=request.author
        )
        created = self.repository.create_rule(rule)
        
        # Save version snapshot
        version = BusinessRuleEngineVersion(
            rule_id=created.id,
            version=1,
            expression_ast=request.expression_ast,
            action=request.action
        )
        self.repository.add_version(version)
        return created

    def evaluate(self, request: RuleEvaluateRequest) -> List[BusinessRuleEngineExecution]:
        rules_to_evaluate = []
        if request.rule_ids:
            for rid in request.rule_ids:
                rule = self.repository.get_rule(rid)
                if rule and rule.status == "ACTIVE":
                    rules_to_evaluate.append(rule)
        else:
            rules_to_evaluate = self.repository.get_active_rules(request.workspace_id)
            
        executions = []
        
        for rule in rules_to_evaluate:
            start_time = time.time()
            try:
                is_match = self.evaluator.evaluate(rule.expression_ast, request.input_objects)
                
                result = "PASS" if is_match else "FAIL"
                triggered_action = rule.action if is_match else None
                
            except Exception as e:
                result = "ERROR"
                triggered_action = None
                
            latency = int((time.time() - start_time) * 1000)
            
            execution = BusinessRuleEngineExecution(
                rule_id=rule.id,
                workspace_id=request.workspace_id,
                input_objects=request.input_objects,
                evaluation_result=result,
                triggered_action=triggered_action,
                execution_time_ms=latency
            )
            self.repository.add_execution(execution)
            executions.append(execution)
            
            self.repository.log_metrics(RuleMetrics(
                workspace_id=request.workspace_id,
                rule_id=rule.id,
                execution_time_ms=latency,
                result=result
            ))
            
        return executions

    def get_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        return self.repository.get_rule(rule_id)
        
    def list_by_workspace(self, workspace_id: str) -> List[RuleDefinition]:
        return self.repository.list_rules(workspace_id)
