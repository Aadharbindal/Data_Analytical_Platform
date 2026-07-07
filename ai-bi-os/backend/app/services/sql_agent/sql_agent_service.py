from sqlalchemy.orm import Session
from typing import List
import time

from app.repositories.sql_agent_repository import SQLAgentRepository
from app.schemas.sql_agent import (
    SQLQueryRequest, SQLQueryResponse,
    SQLValidationRequest, SQLExecutionRequest, SQLExecutionResponse,
    SchemaMetadataResponse, BusinessGlossaryEntry
)

from .intent_analyzer import IntentAnalyzer
from .schema_explorer import SchemaExplorer
from .business_term_resolver import BusinessTermResolver
from .sql_planner import SQLPlanner
from .sql_generator import SQLGenerator
from .sql_optimizer import SQLOptimizer
from .sql_validator import SQLValidator
from .sql_executor import SQLExecutor
from .result_formatter import ResultFormatter
from .sql_cache import SQLCache

class SQLAgentService:
    def __init__(self, db: Session):
        self.repo = SQLAgentRepository(db)
        
        self.intent_analyzer = IntentAnalyzer()
        self.schema_explorer = SchemaExplorer(self.repo)
        self.term_resolver = BusinessTermResolver(self.repo)
        self.planner = SQLPlanner()
        self.generator = SQLGenerator()
        self.optimizer = SQLOptimizer()
        self.validator = SQLValidator()
        self.executor = SQLExecutor()
        self.formatter = ResultFormatter()
        self.cache = SQLCache()

    def generate_query(self, request: SQLQueryRequest) -> SQLQueryResponse:
        # 1. Analyze Intent
        intent = self.intent_analyzer.analyze(request.user_request)
        
        # 2. Explore Schema & Terms
        schema = self.schema_explorer.get_schema(request.workspace_id)
        terms = self.term_resolver.resolve(request.workspace_id, request.user_request)
        
        # 3. Plan SQL
        plan = self.planner.plan_query(intent, schema, terms)
        
        # 4. Generate & Optimize SQL
        raw_sql = self.generator.generate(plan, request.dialect)
        optimized_sql = self.optimizer.optimize(raw_sql, request.dialect)
        
        # 5. Validate Safety
        is_safe, rejection_reason = self.validator.validate(optimized_sql)
        if not is_safe:
            raise ValueError(f"Unsafe SQL generated: {rejection_reason}")
            
        # 6. Save Query
        query = self.repo.save_query(
            workspace_id=request.workspace_id,
            user_request=request.user_request,
            generated_sql=optimized_sql,
            dialect=request.dialect,
            detected_intent=intent
        )
        
        # Record validation
        self.repo.save_validation(query.id, is_safe, rejection_reason)
        
        return SQLQueryResponse.model_validate(query)

    def validate_sql(self, request: SQLValidationRequest) -> bool:
        is_safe, reason = self.validator.validate(request.generated_sql)
        if not is_safe:
            raise ValueError(f"Unsafe SQL: {reason}")
        return True

    def execute_query(self, request: SQLExecutionRequest) -> SQLExecutionResponse:
        start_time = time.time()
        
        query = self.repo.get_query(request.query_id)
        if not query:
            raise ValueError("Query not found")
            
        if not query.is_validated:
            raise ValueError("Cannot execute unvalidated query")
            
        execution = self.repo.create_execution(query.id)
        
        try:
            self.repo.update_execution(execution.id, status="RUNNING")
            
            raw_data = self.executor.execute(query.generated_sql, query.dialect)
            formatted = self.formatter.format(raw_data)
            
            latency = int((time.time() - start_time) * 1000)
            
            self.repo.update_execution(
                execution.id,
                status="COMPLETED",
                execution_time_ms=latency,
                rows_returned=formatted.get("row_count", 0)
            )
            
            return SQLExecutionResponse(
                execution_id=execution.id,
                query_id=query.id,
                generated_sql=query.generated_sql,
                status="COMPLETED",
                rows_returned=formatted.get("row_count", 0),
                execution_time_ms=latency,
                data=formatted.get("data", [])
            )
            
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            self.repo.update_execution(
                execution.id,
                status="FAILED",
                error_message=str(e),
                execution_time_ms=latency
            )
            raise ValueError(f"Execution failed: {str(e)}")

    def get_history(self) -> List[SQLQueryResponse]:
        history = self.repo.get_history()
        return [SQLQueryResponse.model_validate(q) for q in history]

    def get_schema(self, workspace_id: str) -> List[SchemaMetadataResponse]:
        return self.schema_explorer.get_schema(workspace_id)

    def get_glossary(self, workspace_id: str) -> List[BusinessGlossaryEntry]:
        glossary = self.repo.get_glossary(workspace_id)
        return [
            BusinessGlossaryEntry(
                workspace_id=g.workspace_id,
                term=g.term,
                description=g.description,
                mapped_schema=g.mapped_schema,
                mapped_table=g.mapped_table,
                mapped_column=g.mapped_column
            )
            for g in glossary
        ]
