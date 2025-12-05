"""
Health Check & Metrics Routes
"""

from fastapi import APIRouter
from datetime import datetime

from app.schemas import HealthResponse, MCPServerHealth
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    System health check
    """
    try:
        # Check MCP server availability
        from app.mcp_server import mcp
        mcp_available = mcp is not None
    except Exception:
        mcp_available = False
    
    status = "healthy" if mcp_available else "degraded"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database="connected",
        mcp_servers={
            "rag": "healthy" if mcp_available else "unhealthy",
            "sql": "healthy" if mcp_available else "unhealthy",
            "web": "healthy" if mcp_available else "unhealthy",
            "weather": "healthy" if mcp_available else "unhealthy"
        }
    )


@router.get("/mcp/health", response_model=MCPServerHealth)
async def mcp_health():
    """
    Detailed MCP server health status
    """
    try:
        from app.mcp_server import mcp
        mcp_available = mcp is not None
    except Exception:
        mcp_available = False
    
    status = "healthy" if mcp_available else "unhealthy"
    
    return MCPServerHealth(
        rag_server=status,
        sql_server=status,
        web_server=status,
        weather_server=status
    )
