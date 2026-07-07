import time
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.conversation import (
    Conversation, ConversationSession, ConversationMessage, 
    ConversationState, ConversationHistory, ConversationMetrics
)
from app.schemas.conversation import (
    ConversationCreateRequest, MessageRequest, ConversationStateUpdateRequest
)
from app.repositories.conversation_repository import ConversationRepository

class ConversationCache:
    """In-memory cache acting as a fallback for Redis-based session caching."""
    _cache = {}
    
    @classmethod
    def get(cls, key: str):
        return cls._cache.get(key)
        
    @classmethod
    def set(cls, key: str, value: Any):
        cls._cache[key] = value

class SessionManager:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository
        
    def create_session(self, conversation_id: str, workspace_id: str, user_id: Optional[str] = None) -> ConversationSession:
        session = ConversationSession(
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            user_id=user_id
        )
        self.repository.create_session(session)
        ConversationCache.set(f"session_{session.id}", session)
        return session

class ConversationStateMachine:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository
        
    def transition(self, session_id: str, new_state: str, details: Optional[Dict[str, Any]] = None):
        # Validation could be added here (e.g. IDLE -> PLANNING)
        state = ConversationState(session_id=session_id, state_name=new_state, details=details)
        self.repository.update_state(state)

class ContextWindowManager:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository
        self.max_tokens = 100000 # Default limit
        
    def retrieve_context(self, conversation_id: str) -> List[ConversationMessage]:
        # Simple retrieval: fetch all messages and assume they fit. 
        # A real implementation would count tokens and truncate old ones.
        return self.repository.get_messages(conversation_id)

class StreamingManager:
    """Simulates an SSE stream generation. Does no reasoning."""
    async def generate_mock_stream(self, text: str):
        words = text.split()
        for word in words:
            yield f"data: {word} \n\n"
            await asyncio.sleep(0.05)
        yield "data: [DONE]\n\n"

class MessageRouter:
    """Routes messages to orchestrators."""
    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    def route_message(self, message_req: MessageRequest) -> ConversationMessage:
        user_msg = ConversationMessage(
            conversation_id=message_req.conversation_id,
            role=message_req.role,
            content=message_req.content
        )
        self.repository.add_message(user_msg)
        return user_msg
        
    def save_assistant_response(self, conversation_id: str, content: str):
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=content
        )
        self.repository.add_message(msg)

class ConversationManager:
    """High level orchestrator service."""
    def __init__(self, db: Session):
        self.db = db
        self.repository = ConversationRepository(db)
        self.session_manager = SessionManager(self.repository)
        self.state_machine = ConversationStateMachine(self.repository)
        self.context_manager = ContextWindowManager(self.repository)
        self.router = MessageRouter(self.repository)
        self.streamer = StreamingManager()

    def create_conversation(self, request: ConversationCreateRequest) -> Conversation:
        conv = Conversation(
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            conversation_type=request.conversation_type,
            title=request.title or "New Conversation"
        )
        created = self.repository.create_conversation(conv)
        self.repository.add_history(ConversationHistory(conversation_id=created.id, event="CREATE"))
        
        # Auto start a session
        self.session_manager.create_session(created.id, request.workspace_id, request.user_id)
        
        return created

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.repository.get_conversation(conversation_id)

    def archive(self, conversation_id: str):
        conv = self.repository.get_conversation(conversation_id)
        if conv and conv.status != "ARCHIVED":
            conv.status = "ARCHIVED"
            self.repository.update_conversation(conv)
            self.repository.add_history(ConversationHistory(conversation_id=conv.id, event="ARCHIVE"))

    def restore(self, conversation_id: str):
        conv = self.repository.get_conversation(conversation_id)
        if conv and conv.status == "ARCHIVED":
            conv.status = "OPEN"
            self.repository.update_conversation(conv)
            self.repository.add_history(ConversationHistory(conversation_id=conv.id, event="RESTORE"))

    def close(self, conversation_id: str):
        conv = self.repository.get_conversation(conversation_id)
        if conv and conv.status != "CLOSED":
            conv.status = "CLOSED"
            self.repository.update_conversation(conv)
            self.repository.add_history(ConversationHistory(conversation_id=conv.id, event="CLOSE"))
