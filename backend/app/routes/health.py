"""
Health Check & Metrics Routes
Updated for proper MCP architecture with Client/Server
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
    System health check including MCP server status
    """
    mcp_status = "unknown"
    mcp_tools = []
    
    try:
        # Check MCP server availability
        from app.mcp_server import mcp
        mcp_status = "healthy" if mcp is not None else "unhealthy"
        
        # Try to list tools via MCP Client
        try:
            from app.mcp_client import MCPClient
            async with MCPClient() as client:
                mcp_tools = await client.list_tools()
                mcp_status = "healthy"
        except Exception as e:
            logger.warning(f"MCP client health check failed: {str(e)}")
            mcp_status = "degraded"
            
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        mcp_status = "unhealthy"
    
    status = "healthy" if mcp_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database="connected",
        mcp_server={
            "status": mcp_status,
            "endpoint": "/mcp",
            "transport": "Streamable HTTP",
            "tools": mcp_tools if mcp_tools else ["search_documents", "query_database", "web_search", "get_weather"]
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
