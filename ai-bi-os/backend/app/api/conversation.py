import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.schemas.conversation import (
    ConversationCreateRequest,
    MessageRequest,
    ConversationResponse,
    MessageResponse,
    ConversationListResponse
)
from app.services.conversation.conversation_manager import ConversationManager
from app.models.conversation import ConversationMetrics

router = APIRouter(prefix="/conversation", tags=["conversation-engine"])

@router.post("/create", response_model=ConversationResponse)
def create_conversation(request: ConversationCreateRequest, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    try:
        conv = manager.create_conversation(request)
        return conv
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/list", response_model=ConversationListResponse)
def list_conversations(workspace_id: str, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    conversations = manager.repository.list_conversations(workspace_id, skip, limit)
    total = manager.repository.count_conversations(workspace_id)
    return ConversationListResponse(conversations=conversations, total=total)

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    conv = manager.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.get("/history/{conversation_id}", response_model=List[MessageResponse])
def get_conversation_history(conversation_id: str, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    messages = manager.context_manager.retrieve_context(conversation_id)
    return messages

@router.post("/message")
async def send_message(request: MessageRequest, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    
    # Ensure conversation exists
    conv = manager.get_conversation(request.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # Route user message
    manager.router.route_message(request)
    
    # State update
    session = conv.sessions[-1] if conv.sessions else None
    if session:
        manager.state_machine.transition(session.id, "EXECUTING")
    
    # This is where it would normally call Orchestrator Engine for AI reasoning.
    # We will simulate a response stream.
    mock_ai_response = f"This is an AI response to your message: '{request.content}'. The Conversation Engine is handling the streaming successfully."
    
    # Stream wrapper to also save the final text
    async def event_generator():
        start_time = time.time()
        token_count = 0
        if session:
            manager.state_machine.transition(session.id, "STREAMING")
            
        async for chunk in manager.streamer.generate_mock_stream(mock_ai_response):
            token_count += 1
            yield chunk
            
        # Save assistant message once done
        manager.router.save_assistant_response(request.conversation_id, mock_ai_response)
        
        if session:
            manager.state_machine.transition(session.id, "COMPLETED")
            latency = (time.time() - start_time) * 1000
            manager.repository.log_metrics(ConversationMetrics(
                session_id=session.id,
                metric_type="STREAMING_LATENCY",
                value=latency
            ))
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/archive")
def archive_conversation(conversation_id: str, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    manager.archive(conversation_id)
    return {"status": "SUCCESS"}

@router.post("/restore")
def restore_conversation(conversation_id: str, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    manager.restore(conversation_id)
    return {"status": "SUCCESS"}

@router.post("/close")
def close_conversation(conversation_id: str, db: Session = Depends(get_db)):
    manager = ConversationManager(db)
    manager.close(conversation_id)
    return {"status": "SUCCESS"}
