"""
All API routes in one file.
Includes: Authentication, Chat, Health checks.
"""
from datetime import datetime
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import User, ChatMessage
from schemas import (
    UserRegister, UserLogin, Token, UserResponse,
    ChatRequest, ChatResponse, ChatHistoryResponse,
    HealthResponse
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_allowed_departments
)
from agent import AgentService
from metrics import queries_total, query_duration_seconds
from logger import log_info, log_error, set_request_context
from exceptions import AuthenticationError, ValidationError
import time
import json
import asyncio

# ============================================================================
# ROUTERS
# ============================================================================

auth_router = APIRouter()
chat_router = APIRouter()
health_router = APIRouter()

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if username exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise ValidationError("Username already exists", field="username")
    
    # Check if email exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise ValidationError("Email already exists", field="email")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        department=user_data.department,
        role="employee"
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    log_info("User registered", username=user.username, department=user.department)
    
    return user


@auth_router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get JWT token.
    """
    # Get user
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        log_error("Login failed", username=credentials.username)
        raise AuthenticationError("Invalid username or password")
    
    if user.is_active != "true":
        raise AuthenticationError("Account is disabled")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create token
    token = create_access_token({
        "user_id": user.id,
        "username": user.username,
        "department": user.department,
        "role": user.role
    })
    
    log_info("User logged in", username=user.username)
    
    return Token(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return UserResponse.model_validate(current_user)


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@chat_router.post("/query", response_model=ChatResponse)
async def query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process user query with agent.
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    
    # Set logging context
    set_request_context(user_id=current_user.username)
    
    log_info(
        "Processing query",
        user=current_user.username,
        department=current_user.department,
        query=request.query[:100]
    )
    
    try:
        # Get allowed departments for RBAC
        allowed_departments = get_allowed_departments(current_user.department)
        
        # Initialize agent
        agent = AgentService(
            user_department=current_user.department,
            allowed_departments=allowed_departments
        )
        
        # Execute query
        result = await agent.execute_query(request.query)
        
        # Save user message
        user_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role="user",
            content=request.query
        )
        db.add(user_message)
        
        # Save assistant response
        assistant_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role="assistant",
            content=result["response"],
            tools_used=result["tools_used"]
        )
        db.add(assistant_message)
        
        await db.commit()
        
        # Track metrics
        duration = time.time() - start_time
        queries_total.labels(
            department=current_user.department,
            status="success"
        ).inc()
        query_duration_seconds.labels(
            department=current_user.department
        ).observe(duration)
        
        log_info(
            "Query completed",
            duration=duration,
            tools_used=result["tools_used"]
        )
        
        return ChatResponse(
            response=result["response"],
            sources=result["sources"],
            tools_used=result["tools_used"],
            session_id=session_id
        )
    
    except Exception as e:
        log_error("Query failed", exc_info=True, query=request.query)
        
        queries_total.labels(
            department=current_user.department,
            status="failure"
        ).inc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@chat_router.post("/query-stream")
async def query_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process query with SSE streaming.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    async def event_generator():
        try:
            # Get allowed departments
            allowed_departments = get_allowed_departments(current_user.department)
            
            # Initialize agent
            agent = AgentService(
                user_department=current_user.department,
                allowed_departments=allowed_departments
            )
            
            # Stream: Starting
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing query...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Stream: Tool selection
            yield f"data: {json.dumps({'type': 'status', 'message': 'Selecting tools...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Execute query (this should be made streaming in production)
            result = await agent.execute_query(request.query)
            
            # Stream: Tools used
            if result["tools_used"]:
                yield f"data: {json.dumps({'type': 'tools', 'tools': result['tools_used']})}\n\n"
                await asyncio.sleep(0.1)
            
            # Stream: Sources
            if result["sources"]:
                yield f"data: {json.dumps({'type': 'sources', 'sources': result['sources']})}\n\n"
                await asyncio.sleep(0.1)
            
            # Stream: Response (simulate streaming by breaking into chunks)
            response_text = result["response"]
            chunk_size = 50
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'response_chunk', 'text': chunk})}\n\n"
                await asyncio.sleep(0.05)
            
            # Stream: Done
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
            
            # Save to database
            user_message = ChatMessage(
                user_id=current_user.id,
                session_id=session_id,
                role="user",
                content=request.query
            )
            db.add(user_message)
            
            assistant_message = ChatMessage(
                user_id=current_user.id,
                session_id=session_id,
                role="assistant",
                content=result["response"],
                tools_used=result["tools_used"]
            )
            db.add(assistant_message)
            
            await db.commit()
        
        except Exception as e:
            log_error("Streaming query failed", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@chat_router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    session_id: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history for user.
    """
    query = select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    
    if session_id:
        query = query.where(ChatMessage.session_id == session_id)
    
    query = query.order_by(desc(ChatMessage.timestamp)).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return ChatHistoryResponse(
        messages=messages,
        total=len(messages)
    )


# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@health_router.get("/liveness", response_model=HealthResponse)
async def liveness():
    """
    Liveness probe - is the app running?
    """
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@health_router.get("/readiness", response_model=HealthResponse)
async def readiness(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe - is the app ready to serve traffic?
    """
    checks = {}
    
    # Check database
    try:
        await db.execute(select(1))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    overall_status = "ready" if all(
        c.get("status") == "healthy" for c in checks.values()
    ) else "not_ready"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=checks
    )
