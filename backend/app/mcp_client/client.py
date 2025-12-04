"""
MCP Client - Async HTTP Wrapper for MCP Servers
"""

import httpx
from typing import Dict, Any, Optional
import asyncio

from app.config import settings
from app.logger import get_logger, log_tool_execution
import time

logger = get_logger(__name__)


class MCPClient:
    """
    Generic async HTTP client for MCP servers
    Handles requests, retries, and error handling
    """
    
    def __init__(self, server_url: str, server_name: str):
        """
        Initialize MCP client
        
        Args:
            server_url: Base URL of MCP server
            server_name: Human-readable server name
        """
        self.server_url = server_url
        self.server_name = server_name
        self.timeout = 30.0
        self.max_retries = 2
    
    async def call(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Call MCP server endpoint
        
        Args:
            endpoint: API endpoint (e.g., "/search", "/query")
            payload: Request payload
            query: User query (for logging)
        
        Returns:
            Response data or None if failed
        """
        url = f"{self.server_url}{endpoint}"
        start_time = time.time()
        
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    duration_ms = (time.time() - start_time) * 1000
                    log_tool_execution(
                        logger,
                        tool_name=self.server_name,
                        query=query,
                        result=result,
                        duration_ms=duration_ms,
                        success=result.get("success", True)
                    )
                    
                    return result
                    
            except httpx.TimeoutException:
                logger.warning(
                    f"{self.server_name} timeout (attempt {attempt}/{self.max_retries})"
                )
                if attempt == self.max_retries:
                    logger.error(f"{self.server_name} failed after {self.max_retries} retries")
                    return None
                await asyncio.sleep(1)  # Brief delay before retry
                
            except httpx.HTTPStatusError as e:
                logger.error(f"{self.server_name} HTTP error: {e.response.status_code}")
                return None
                
            except Exception as e:
                logger.error(f"{self.server_name} call failed: {str(e)}")
                return None
        
        return None
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.server_url}/health",
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("status") == "healthy"
        except:
            return False


# =============================================================================
# Specific MCP Clients
# =============================================================================
class RAGClient(MCPClient):
    """RAG MCP client"""
    
    def __init__(self):
        super().__init__(settings.mcp_rag_url, "RAG")
    
    async def search(
        self,
        query: str,
        user_department: str,
        user_role: str,
        user_id: int,
        top_k: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Search documents using hybrid RAG pipeline"""
        return await self.call(
            endpoint="/search",
            payload={
                "query": query,
                "user_department": user_department,
                "user_role": user_role,
                "user_id": user_id,
                "top_k": top_k
            },
            query=query
        )


class SQLClient(MCPClient):
    """SQL MCP client"""
    
    def __init__(self):
        super().__init__(settings.mcp_sql_url, "SQL")
    
    async def query(
        self,
        query: str,
        user_role: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Execute SQL query with RBAC"""
        return await self.call(
            endpoint="/query",
            payload={
                "query": query,
                "user_role": user_role,
                "user_id": user_id
            },
            query=query
        )


class WebClient(MCPClient):
    """Web search MCP client"""
    
    def __init__(self):
        super().__init__(settings.mcp_web_url, "Web")
    
    async def search(
        self,
        query: str,
        user_id: int,
        recency_filter: str = "month"
    ) -> Optional[Dict[str, Any]]:
        """Search web using Tavily"""
        return await self.call(
            endpoint="/search",
            payload={
                "query": query,
                "user_id": user_id,
                "recency_filter": recency_filter
            },
            query=query
        )


class WeatherClient(MCPClient):
    """Weather MCP client"""
    
    def __init__(self):
        super().__init__(settings.mcp_weather_url, "Weather")
    
    async def get_weather(
        self,
        query: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get weather using Open-Meteo"""
        return await self.call(
            endpoint="/weather",
            payload={
                "query": query,
                "user_id": user_id
            },
            query=query
        )


# =============================================================================
# Global client instances
# =============================================================================
rag_client = RAGClient()
sql_client = SQLClient()
web_client = WebClient()
weather_client = WeatherClient()
