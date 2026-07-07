from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ConversationCreateRequest(BaseModel):
    workspace_id: str
    user_id: Optional[str] = None
    conversation_type: str = "General Business Chat"
    title: Optional[str] = None

class MessageRequest(BaseModel):
    conversation_id: str
    content: str
    role: str = "user"

class ConversationStateUpdateRequest(BaseModel):
    session_id: str
    state_name: str
    details: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: Optional[str]
    conversation_type: str
    title: Optional[str]
    summary: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SessionResponse(BaseModel):
    id: str
    conversation_id: str
    status: str
    created_at: datetime
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
