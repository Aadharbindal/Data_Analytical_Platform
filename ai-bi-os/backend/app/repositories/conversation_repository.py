from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from app.models.conversation import (
    Conversation, ConversationSession, ConversationMessage, 
    ConversationState, ConversationHistory, ConversationMetrics
)

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        
    def update_conversation(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def list_conversations(self, workspace_id: str, skip: int = 0, limit: int = 50) -> List[Conversation]:
        return self.db.query(Conversation).filter(
            Conversation.workspace_id == workspace_id
        ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()

    def count_conversations(self, workspace_id: str) -> int:
        return self.db.query(func.count(Conversation.id)).filter(
            Conversation.workspace_id == workspace_id
        ).scalar() or 0

    def add_message(self, message: ConversationMessage) -> ConversationMessage:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
        
    def get_messages(self, conversation_id: str) -> List[ConversationMessage]:
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.asc()).all()

    def create_session(self, session: ConversationSession) -> ConversationSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
        
    def update_state(self, state: ConversationState):
        self.db.add(state)
        self.db.commit()

    def add_history(self, history: ConversationHistory):
        self.db.add(history)
        self.db.commit()
        
    def log_metrics(self, metric: ConversationMetrics):
        self.db.add(metric)
        self.db.commit()
