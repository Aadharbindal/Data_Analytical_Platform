from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.models.sql_agent import (
    SQLQuery, SQLExecution, SQLHistory, SQLValidation,
    SQLMetrics, BusinessGlossary, SchemaMetadata, QueryCache
)

class SQLAgentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_query(self, workspace_id: str, user_request: str, generated_sql: str, dialect: str, detected_intent: str = None) -> SQLQuery:
        query = SQLQuery(
            workspace_id=workspace_id,
            user_request=user_request,
            detected_intent=detected_intent,
            generated_sql=generated_sql,
            dialect=dialect
        )
        self.db.add(query)
        self.db.commit()
        self.db.refresh(query)
        return query

    def get_query(self, query_id: str) -> Optional[SQLQuery]:
        return self.db.query(SQLQuery).filter(SQLQuery.id == query_id).first()

    def save_validation(self, query_id: str, is_safe: bool, rejection_reason: str = None) -> SQLValidation:
        validation = SQLValidation(
            query_id=query_id,
            is_safe=is_safe,
            rejection_reason=rejection_reason
        )
        
        query = self.get_query(query_id)
        if query:
            query.is_validated = is_safe
            self.db.add(query)
            
        self.db.add(validation)
        self.db.commit()
        return validation

    def create_execution(self, query_id: str) -> SQLExecution:
        execution = SQLExecution(query_id=query_id)
        self.db.add(execution)
        self.db.flush()
        
        history = SQLHistory(
            execution_id=execution.id,
            status_to="PENDING"
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_execution(self, execution_id: str, status: str, error_message: str = None, execution_time_ms: int = None, rows_returned: int = 0) -> SQLExecution:
        execution = self.db.query(SQLExecution).filter(SQLExecution.id == execution_id).first()
        if not execution:
            return None
            
        execution.status = status
        if error_message:
            execution.error_message = error_message
            
        if status in ["COMPLETED", "FAILED"]:
            execution.completed_at = datetime.utcnow()
            
            metrics = SQLMetrics(
                execution_id=execution.id,
                execution_time_ms=execution_time_ms,
                rows_returned=rows_returned
            )
            self.db.add(metrics)
            
        self.db.add(execution)
        
        history = SQLHistory(
            execution_id=execution.id,
            status_to=status
        )
        self.db.add(history)
        
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_history(self) -> List[SQLQuery]:
        return self.db.query(SQLQuery).order_by(desc(SQLQuery.created_at)).limit(100).all()

    def get_glossary(self, workspace_id: str) -> List[BusinessGlossary]:
        return self.db.query(BusinessGlossary).filter(BusinessGlossary.workspace_id == workspace_id, BusinessGlossary.is_active == True).all()

    def get_schema_metadata(self, workspace_id: str) -> List[SchemaMetadata]:
        return self.db.query(SchemaMetadata).filter(SchemaMetadata.workspace_id == workspace_id).all()
