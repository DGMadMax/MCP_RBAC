"""
Health Check & Metrics Routes
"""

from fastapi import APIRouter
from datetime import datetime
import asyncio

from app.mcp_client import rag_client, sql_client, web_client, weather_client
from app.schemas import HealthResponse, MCPServerHealth
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    System health check
    Checks main application and all MCP servers
    """
    # Check MCP servers in parallel
    health_checks = await asyncio.gather(
        rag_client.health_check(),
        sql_client.health_check(),
        web_client.health_check(),
        weather_client.health_check(),
        return_exceptions=True
    )
    
    rag_status = "healthy" if health_checks[0] else "unhealthy"
    sql_status = "healthy" if health_checks[1] else "unhealthy"
    web_status = "healthy" if health_checks[2] else "unhealthy"
    weather_status = "healthy" if health_checks[3] else "unhealthy"
    
    # Overall status
    all_healthy = all([
        health_checks[0],
        health_checks[1],
        health_checks[2],
        health_checks[3]
    ])
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow(),
        database="connected",
        mcp_servers={
            "rag": rag_status,
            "sql": sql_status,
            "web": web_status,
            "weather": weather_status
        }
    )


@router.get("/mcp/health", response_model=MCPServerHealth)
async def mcp_health():
    """
    Detailed MCP server health status
    """
    health_checks = await asyncio.gather(
        rag_client.health_check(),
        sql_client.health_check(),
        web_client.health_check(),
        weather_client.health_check(),
        return_exceptions=True
    )
    
    return MCPServerHealth(
        rag_server="healthy" if health_checks[0] else "unhealthy",
        sql_server="healthy" if health_checks[1] else "unhealthy",
        web_server="healthy" if health_checks[2] else "unhealthy",
        weather_server="healthy" if health_checks[3] else "unhealthy"
    )
