"""
Unit Tests for MCP Client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx


class TestMCPClient:
    """Test base MCP Client"""
    
    @pytest.mark.asyncio
    async def test_mcp_client_success(self):
        """Test successful MCP client call"""
        from app.mcp_client.client import MCPClient
        
        client = MCPClient("http://localhost:8001", "TestServer")
        
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.call(
                endpoint="/test",
                payload={"query": "test"},
                query="test query"
            )
            
            assert result is not None
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_client_timeout(self):
        """Test MCP client timeout handling"""
        from app.mcp_client.client import MCPClient
        
        client = MCPClient("http://localhost:8001", "TestServer")
        client.max_retries = 1  # Reduce retries for faster test
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            result = await client.call(
                endpoint="/test",
                payload={"query": "test"},
                query="test query"
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_mcp_client_http_error(self):
        """Test MCP client HTTP error handling"""
        from app.mcp_client.client import MCPClient
        
        client = MCPClient("http://localhost:8001", "TestServer")
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.call(
                endpoint="/test",
                payload={"query": "test"},
                query="test query"
            )
            
            assert result is None


class TestRAGClient:
    """Test RAG MCP Client"""
    
    @pytest.mark.asyncio
    async def test_rag_client_search(self, mock_rag_results):
        """Test RAG client search"""
        from app.mcp_client.client import RAGClient
        
        client = RAGClient()
        
        mock_response = Mock()
        mock_response.json.return_value = mock_rag_results
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.search(
                query="test query",
                user_department="engineering",
                user_role="Engineering Team",
                user_id=1,
                top_k=3
            )
            
            assert result is not None
            assert result["success"] is True
            assert len(result["results"]) == 2


class TestSQLClient:
    """Test SQL MCP Client"""
    
    @pytest.mark.asyncio
    async def test_sql_client_query(self, mock_sql_results):
        """Test SQL client query"""
        from app.mcp_client.client import SQLClient
        
        client = SQLClient()
        
        mock_response = Mock()
        mock_response.json.return_value = mock_sql_results
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.query(
                query="Show me all employees",
                user_role="HR Team",
                user_id=1
            )
            
            assert result is not None
            assert result["success"] is True
            assert "sql" in result


class TestWebClient:
    """Test Web Search MCP Client"""
    
    @pytest.mark.asyncio
    async def test_web_client_search(self, mock_web_results):
        """Test web search client"""
        from app.mcp_client.client import WebClient
        
        client = WebClient()
        
        mock_response = Mock()
        mock_response.json.return_value = mock_web_results
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.search(
                query="latest Python version",
                user_id=1,
                recency_filter="month"
            )
            
            assert result is not None
            assert result["success"] is True
            assert len(result["sources"]) > 0


class TestWeatherClient:
    """Test Weather MCP Client"""
    
    @pytest.mark.asyncio
    async def test_weather_client_get_weather(self, mock_weather_results):
        """Test weather client"""
        from app.mcp_client.client import WeatherClient
        
        client = WeatherClient()
        
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_results
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await client.get_weather(
                query="What's the weather in Bangalore?",
                user_id=1
            )
            
            assert result is not None
            assert result["success"] is True
            assert result["city"] == "Bangalore"
            assert result["temperature"] == 24.5
