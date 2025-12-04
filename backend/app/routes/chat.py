"""
Chat Routes - Main Chat Endpoints with SSE Streaming
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio
from datetime import datetime

from app.database import get_db
from app.models import User, ChatHistory
from app.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from app.auth import get_current_user
from app.agent import agent_graph, agent_memory
from app.agent.state import AgentState
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_last_n_messages(user_id: int, db: Session, n: int = 4):
    """
    Get last N chat messages for user
    
    Args:
        user_id: User ID
        db: Database session
        n: Number of messages to retrieve
    
    Returns:
        List of chat messages
    """
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).order_by(
        ChatHistory.created_at.desc()
    ).limit(n).all()
    
    return [
        {"query": h.query, "response": h.response}
        for h in reversed(history)
    ]


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with SSE streaming
    
    Streams real-time updates:
    - Status updates (classifying, searching, generating)
    - LLM response chunks
    - Tool execution metadata
    - Final sources/citations
    """
    async def event_generator():
        try:
            # Build initial state
            chat_history = get_last_n_messages(user.id, db, n=4)
            
            state: AgentState = {
                "user_id": user.id,
                "user_role": user.role,
                "user_department": user.department,
                "original_query": request.query,
                "rewritten_queries": [],
                "is_multi_query": False,
                "chat_history": chat_history,
                "intent": "",
                "tools_to_call": [],
                "rag_results": None,
                "sql_results": None,
                "web_results": None,
                "weather_results": None,
                "final_response": "",
                "sources": [],
                "confidence": "",
                "status_updates": [],
                "current_stage": "orchestrating"
            }
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing your question...'})}\n\n"
            
            # Execute agent graph with streaming
            config = {"configurable": {"thread_id": str(user.id)}}
            
            async for event in agent_graph.astream(state, config=config):
                node_name = list(event.keys())[0]
                node_state = event[node_name]
                
                # Send status updates based on stage
                if node_name == "orchestrator":
                    intent = node_state.get("intent", "")
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Intent: {intent}'})}\n\n"
                
                elif node_name == "query_rewriter":
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Refining query...'})}\n\n"
                
                elif node_name == "tool_executor":
                    tools = node_state.get("tools_to_call", [])
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Using tools: {tools}'})}\n\n"
                    
                    # Send tool results
                    for tool in tools:
                        result_key = f"{tool}_results"
                        if node_state.get(result_key):
                            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool})}\n\n"
                
                elif node_name == "synthesizer":
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...'})}\n\n"
                    
                    # Stream response in chunks
                    response = node_state.get("final_response", "")
                    words = response.split()
                    
                    for i in range(0, len(words), 5):  # Stream 5 words at a time
                        chunk = " ".join(words[i:i+5]) + " "
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                        await asyncio.sleep(0.05)  # Small delay for streaming effect
                    
                    # Send sources
                    sources = node_state.get("sources", [])
                    if sources:
                        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
            # Save to chat history
            final_state = state
            chat_entry = ChatHistory(
                user_id=user.id,
                query=request.query,
                response=final_state["final_response"],
                tools_used=final_state.get("tools_to_call", []),
                sources=final_state.get("sources", []),
                intent=final_state.get("intent", "")
            )
            db.add(chat_entry)
            db.commit()
            
            # Send done event
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
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synchronous chat (non-streaming)
    """
    try:
        # Build state
        chat_history = get_last_n_messages(user.id, db, n=4)
        
        state: AgentState = {
            "user_id": user.id,
            "user_role": user.role,
            "user_department": user.department,
            "original_query": request.query,
            "rewritten_queries": [],
            "is_multi_query": False,
            "chat_history": chat_history,
            "intent": "",
            "tools_to_call": [],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        # Execute agent
        config = {"configurable": {"thread_id": str(user.id)}}
        result = await agent_graph.ainvoke(state, config=config)
        
        # Save to history
        chat_entry = ChatHistory(
            user_id=user.id,
            query=request.query,
            response=result["final_response"],
            tools_used=result.get("tools_to_call", []),
            sources=result.get("sources", []),
            intent=result.get("intent", "")
        )
        db.add(chat_entry)
        db.commit()
        
        logger.info(f"Chat completed for user {user.id}")
        
        return ChatResponse(
            query=request.query,
            response=result["final_response"],
            tools_used=result.get("tools_to_call", []),
            sources=result.get("sources", []),
            intent=result.get("intent", ""),
            confidence=result.get("confidence", "medium"),
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
