"""
Chat Routes - Main Chat Endpoints with SSE Streaming and Rate Limiting
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import asyncio
from datetime import datetime

from app.database import get_db
from app.models import User, ChatHistory
from app.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from app.auth import get_current_user
from app.agent.graph import run_agent
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Rate limiter - uses the limiter from main.py
limiter = Limiter(key_func=get_remote_address)


def get_chat_history_messages(user_id: int, db: Session, n: int = 6):
    """
    Get last N chat messages for user as LangChain messages.
    """
    from langchain_core.messages import HumanMessage, AIMessage
    
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).order_by(
        ChatHistory.created_at.desc()
    ).limit(n).all()
    
    messages = []
    for h in reversed(history):
        messages.append(HumanMessage(content=h.query))
        messages.append(AIMessage(content=h.response))
    
    return messages


@router.post("/stream")
@limiter.limit(f"{settings.rate_limit_per_user}/minute")
async def stream_chat(
    request: Request,
    chat_request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with SSE streaming.
    
    Streams real-time updates:
    - Status updates (classifying, searching, generating)
    - Final response
    - Sources/citations
    """
    async def event_generator():
        try:
            # Get chat history
            chat_history = get_chat_history_messages(user.id, db, n=6)
            session_id = f"user_{user.id}_{chat_request.session_id or 'default'}"
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting...'})}\n\n"
            
            # Run agent with streaming
            final_response = ""
            sources = []
            
            async for event in run_agent(
                query=chat_request.query,
                user_id=user.id,
                user_role=user.role,
                user_department=user.department,
                session_id=session_id,
                chat_history=chat_history
            ):
                if event["type"] == "status":
                    yield f"data: {json.dumps({'type': 'status', 'message': event['content']})}\n\n"
                elif event["type"] == "response":
                    final_response = event["content"]
                    sources = event.get("sources", [])
                    
                    # Stream response in chunks
                    words = final_response.split()
                    for i in range(0, len(words), 5):
                        chunk = " ".join(words[i:i+5]) + " "
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                        await asyncio.sleep(0.03)
            
            # Save to chat history
            if final_response:
                chat_entry = ChatHistory(
                    user_id=user.id,
                    query=chat_request.query,
                    response=final_response,
                    tools_used=[],
                    sources=sources,
                    intent=""
                )
                db.add(chat_entry)
                db.commit()
            
            # Send sources and done
            if sources:
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream chat error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("", response_model=ChatResponse)
@limiter.limit(f"{settings.rate_limit_per_user}/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synchronous chat (non-streaming)
    """
    try:
        chat_history = get_chat_history_messages(user.id, db, n=6)
        session_id = f"user_{user.id}_{chat_request.session_id or 'default'}"
        
        final_response = ""
        sources = []
        
        async for event in run_agent(
            query=chat_request.query,
            user_id=user.id,
            user_role=user.role,
            user_department=user.department,
            session_id=session_id,
            chat_history=chat_history
        ):
            if event["type"] == "response":
                final_response = event["content"]
                sources = event.get("sources", [])
        
        # Save to history
        chat_entry = ChatHistory(
            user_id=user.id,
            query=chat_request.query,
            response=final_response,
            tools_used=[],
            sources=sources,
            intent=""
        )
        db.add(chat_entry)
        db.commit()
        
        logger.info(f"Chat completed for user {user.id}")
        
        return ChatResponse(
            query=chat_request.query,
            response=final_response,
            tools_used=[],
            sources=sources,
            intent="",
            confidence="medium",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=list[ChatHistoryResponse])
async def get_chat_history(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's chat history
    """
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == user.id
    ).order_by(
        ChatHistory.created_at.desc()
    ).limit(limit).all()
    
    return [ChatHistoryResponse.from_orm(h) for h in history]
