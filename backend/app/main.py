"""
Main FastAPI Application - RBAC Agentic AI Chatbot
Production-Grade Backend Server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.logger import setup_centralized_logging, shutdown_logging, get_logger
from app.database import init_database
from app.config import settings
from app.routes import auth, chat, health, feedback

# Initialize centralized logging first
setup_centralized_logging()
logger = get_logger(__name__)


# =============================================================================
# Lifespan Context Manager (Startup/Shutdown)
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 Starting RBAC Agentic AI Chatbot...")
    logger.info("=" * 80)
    
    # Initialize database
    init_database()
    logger.info("✅ Database initialized")
    
    # Check MCP server connectivity
    logger.info("Checking MCP server connectivity...")
    from app.mcp_client import rag_client, sql_client, web_client, weather_client
    import asyncio
    
    health_checks = await asyncio.gather(
        rag_client.health_check(),
        sql_client.health_check(),
        web_client.health_check(),
        weather_client.health_check(),
        return_exceptions=True
    )
    
    logger.info(f"  RAG Server: {'✅' if health_checks[0] else '❌'}")
    logger.info(f"  SQL Server: {'✅' if health_checks[1] else '❌'}")
    logger.info(f"  Web Server: {'✅' if health_checks[2] else '❌'}")
    logger.info(f"  Weather Server: {'✅' if health_checks[3] else '❌'}")
    
    if not all(health_checks):
        logger.warning("⚠️ Some MCP servers are not responding!")
        logger.warning("Make sure to start MCP servers: python -m app.mcp_servers")
    
    logger.info("=" * 80)
    logger.info("✅ Application ready!")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    shutdown_logging()


# =============================================================================
# FastAPI Application
# =============================================================================
app = FastAPI(
    title="RBAC Agentic AI Chatbot",
    description="Production-grade agentic chatbot with hybrid RAG, SQL, Web Search, and Weather tools",
    version="1.0.0",
    lifespan=lifespan
)


# =============================================================================
# CORS Middleware
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/auth",
            "chat": "/chat",
            "health": "/health",
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
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
