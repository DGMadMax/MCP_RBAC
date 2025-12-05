"""
MCP Client - Official SDK Implementation
Uses ClientSession with Streamable HTTP transport to connect to MCP Server

This is the proper way to call MCP tools according to the official MCP SDK:
https://github.com/modelcontextprotocol/python-sdk

The client connects to the MCP server at /mcp endpoint and uses JSON-RPC
to call tools via session.call_tool()
"""

import asyncio
from typing import Any, Dict, Optional
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

from app.logger import get_logger

logger = get_logger(__name__)

# MCP Server URL (internal service - same application)
MCP_SERVER_URL = "http://localhost:8000/mcp"


class MCPClient:
    """
    Official MCP Client using ClientSession.
    
    Usage:
        async with MCPClient() as client:
            tools = await client.list_tools()
            result = await client.call_tool("search_documents", {...})
    """
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url or MCP_SERVER_URL
        self.session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._client_context = None
        self._session_context = None
    
    async def __aenter__(self):
        """Connect to MCP server and initialize session."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup session and connection."""
        await self.disconnect()
    
    async def connect(self):
        """
        Connect to the MCP server using Streamable HTTP transport.
        """
        try:
            logger.info(f"[MCP Client] Connecting to {self.server_url}")
            
            # Create the streamable HTTP client context
            self._client_context = streamablehttp_client(self.server_url)
            self._read_stream, self._write_stream, _ = await self._client_context.__aenter__()
            
            # Create session
            self._session_context = ClientSession(self._read_stream, self._write_stream)
            self.session = await self._session_context.__aenter__()
            
            # Initialize the connection
            await self.session.initialize()
            
            logger.info("[MCP Client] Connected and initialized")
            
        except Exception as e:
            logger.error(f"[MCP Client] Connection failed: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._client_context:
                await self._client_context.__aexit__(None, None, None)
            logger.info("[MCP Client] Disconnected")
        except Exception as e:
            logger.error(f"[MCP Client] Disconnect error: {str(e)}")
    
    async def list_tools(self) -> list:
        """
        List all available tools from the MCP server.
        
        Returns:
            List of tool names
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        tools_response = await self.session.list_tools()
        tools = [tool.name for tool in tools_response.tools]
        logger.info(f"[MCP Client] Available tools: {tools}")
        return tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Tool result as string
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        logger.info(f"[MCP Client] Calling tool: {tool_name}")
        logger.debug(f"[MCP Client] Arguments: {arguments}")
        
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            
            # Extract text content from result
            if result.content:
                content = result.content[0]
                if isinstance(content, types.TextContent):
                    return content.text
                elif hasattr(content, 'text'):
                    return content.text
                else:
                    return str(content)
            
            # Check for structured content
            if result.structuredContent:
                return str(result.structuredContent)
            
            return "No result returned from tool"
            
        except Exception as e:
            logger.error(f"[MCP Client] Tool call failed: {str(e)}")
            return f"Error calling tool: {str(e)}"


# =============================================================================
# Convenience functions for calling tools
# =============================================================================
async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Convenience function to call an MCP tool.
    Creates a new connection for each call (stateless).
    
    Args:
        tool_name: Name of the tool
        arguments: Tool arguments
        
    Returns:
        Tool result as string
    """
    async with MCPClient() as client:
        return await client.call_tool(tool_name, arguments)


# Specific tool wrappers for backward compatibility
async def search_documents(query: str, department: str, user_role: str, top_k: int = 3) -> str:
    """Search documents via MCP."""
    return await call_mcp_tool("search_documents", {
        "query": query,
        "department": department,
        "user_role": user_role,
        "top_k": top_k
    })


async def query_database(query: str, user_role: str, user_id: int) -> str:
    """Query database via MCP."""
    return await call_mcp_tool("query_database", {
        "query": query,
        "user_role": user_role,
        "user_id": user_id
    })


async def web_search(query: str, max_results: int = 5) -> str:
    """Web search via MCP."""
    return await call_mcp_tool("web_search", {
        "query": query,
        "max_results": max_results
    })


async def get_weather(city: str, unit: str = "celsius") -> str:
    """Get weather via MCP."""
    return await call_mcp_tool("get_weather", {
        "city": city,
        "unit": unit
    })
