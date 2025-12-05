"""
Main FastAPI Application - RBAC Agentic AI Chatbot
Production-Grade Backend Server with Rate Limiting and MCP Server

MCP Server is mounted at /mcp for Streamable HTTP transport.
MCP Client connects to /mcp to call tools via JSON-RPC.
"""

import contextlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from starlette.routing import Mount
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.logger import setup_centralized_logging, shutdown_logging, get_logger
from app.database import init_database
from app.config import settings
from app.routes import auth, chat, health, feedback
from app.mcp_server import mcp, get_mcp_app

# Initialize centralized logging first
setup_centralized_logging()
logger = get_logger(__name__)

# =============================================================================
# Rate Limiter Setup
# =============================================================================
def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting.
    Uses user ID from JWT token if available, otherwise falls back to IP.
    """
    # Try to get user from request state (set by auth dependency)
    if hasattr(request.state, 'user') and request.state.user:
        return f"user_{request.state.user.id}"
    # Fall back to IP address
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_identifier)


# =============================================================================
# Lifespan Context Manager (Startup/Shutdown)
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Handles startup and shutdown events including MCP session manager
    """
    # Startup
    logger.info("=" * 80)
    logger.info("Starting RBAC Agentic AI Chatbot...")
    logger.info("=" * 80)
    
    # Initialize database
    init_database()
    logger.info("[OK] Database initialized")
    
    # Start MCP session manager
    logger.info("Starting MCP Server session manager...")
    async with mcp.session_manager.run():
        logger.info(f"[OK] MCP Server: {mcp.name} loaded with tools")
        logger.info("[OK] MCP Endpoint: http://localhost:8000/mcp")
        
        # Log rate limiting config
        logger.info(f"[OK] Rate limiting: {settings.rate_limit_per_user} requests per user per minute")
        
        logger.info("=" * 80)
        logger.info("[OK] Application ready!")
        logger.info("=" * 80)
        
        yield
    
    # Shutdown
    logger.info("[STOP] Shutting down application...")
    shutdown_logging()


# =============================================================================
# FastAPI Application
# =============================================================================
app = FastAPI(
    title="RBAC Agentic AI Chatbot",
    description="Production-grade agentic chatbot with hybrid RAG, SQL, Web Search, and Weather tools",
    version="2.0.0",
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =============================================================================
# CORS Middleware
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Required for MCP browser clients to access session ID
    expose_headers=["Mcp-Session-Id"],
)


# =============================================================================
# Mount MCP Server at /mcp
# =============================================================================
# The MCP server handles JSON-RPC requests via Streamable HTTP transport
# MCP Client connects here to call tools like search_documents, query_database, etc.
app.mount("/mcp", get_mcp_app())


# =============================================================================
# Register Routes
# =============================================================================
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(health.router)
app.include_router(feedback.router)


# =============================================================================
# Root Endpoint
# =============================================================================
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "RBAC Agentic AI Chatbot",
        "version": "2.0.0",
        "status": "running",
        "architecture": "MCP + LangGraph",
        "mcp_endpoint": "/mcp",
        "mcp_transport": "Streamable HTTP",
        "rate_limit": f"{settings.rate_limit_per_user}/minute",
        "endpoints": {
            "auth": "/auth",
            "chat": "/chat",
            "health": "/health",
            "mcp": "/mcp",
            "docs": "/docs"
        }
    }


# =============================================================================
# Run Application
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
