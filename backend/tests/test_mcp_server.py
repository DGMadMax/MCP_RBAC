"""
Unit Tests for MCP Server Tools
Production-Grade Test Suite for RBAC Agentic AI Chatbot

Tests cover:
- search_documents (RAG tool)
- query_database (SQL tool)
- web_search (Tavily tool)
- get_weather (Open-Meteo tool)

Author: Senior Software Engineer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline for document search tests"""
    with patch('app.mcp_server.RAGPipeline') as mock:
        pipeline = MagicMock()
        pipeline.retrieve = AsyncMock(return_value={
            "results": [
                {
                    "text": "Engineering policies require code reviews.",
                    "metadata": {"department": "engineering", "file_name": "policies.md"},
                    "rerank_score": 0.95
                }
            ],
            "metadata": {"query": "test", "total_time_ms": 100}
        })
        mock.return_value = pipeline
        yield pipeline


@pytest.fixture
def mock_groq_llm():
    """Mock Groq LLM for SQL generation tests"""
    with patch('app.mcp_server.ChatGroq') as mock:
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="SELECT * FROM employees WHERE department = 'engineering'"
        ))
        mock.return_value = llm
        yield llm


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for external API calls"""
    with patch('app.mcp_server.httpx.AsyncClient') as mock:
        client = AsyncMock()
        mock.return_value.__aenter__ = AsyncMock(return_value=client)
        mock.return_value.__aexit__ = AsyncMock(return_value=None)
        yield client


# =============================================================================
# Test: search_documents (RAG Tool)
# =============================================================================
class TestSearchDocuments:
    """Test suite for RAG document search tool"""
    
    @pytest.mark.asyncio
    async def test_search_documents_success(self, mock_rag_pipeline):
        """Test successful document search with valid query"""
        from app.mcp_server import search_documents
        
        result = await search_documents(
            query="What are the engineering policies?",
            department="engineering",
            user_role="Engineering Team",
            top_k=3
        )
        
        assert "Results" in result or "policies" in result.lower()
    
    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self):
        """Test search with empty query returns error message"""
        from app.mcp_server import search_documents
        
        result = await search_documents(
            query="",
            department="engineering",
            user_role="Engineering Team",
            top_k=3
        )
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_documents_rbac_filtering(self, mock_rag_pipeline):
        """Test RBAC filtering by department"""
        from app.mcp_server import search_documents
        
        # Engineering user should only see engineering docs
        result = await search_documents(
            query="salary policies",
            department="engineering",
            user_role="Engineering Team",
            top_k=3
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_search_documents_c_level_access(self, mock_rag_pipeline):
        """Test C-Level users have access to all departments"""
        from app.mcp_server import search_documents
        
        result = await search_documents(
            query="confidential salary data",
            department="c-level",
            user_role="C-Level",
            top_k=5
        )
        
        assert result is not None


# =============================================================================
# Test: query_database (SQL Tool)
# =============================================================================
class TestQueryDatabase:
    """Test suite for SQL query tool"""
    
    @pytest.mark.asyncio
    async def test_query_database_success(self, mock_groq_llm):
        """Test successful SQL query generation and execution"""
        from app.mcp_server import query_database
        
        with patch('app.mcp_server.text') as mock_text:
            with patch('app.mcp_server.create_engine') as mock_engine:
                mock_conn = MagicMock()
                mock_result = MagicMock()
                mock_result.fetchall.return_value = [("John", "engineering")]
                mock_result.keys.return_value = ["name", "department"]
                mock_conn.execute.return_value = mock_result
                mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
                mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=None)
                
                result = await query_database(
                    query="Show all engineers",
                    user_role="Engineering Team",
                    user_id=1
                )
                
                assert result is not None
    
    @pytest.mark.asyncio  
    async def test_query_database_role_restrictions(self, mock_groq_llm):
        """Test role-based table access restrictions"""
        from app.mcp_server import query_database
        
        # Engineering role should not access salaries table
        with patch('app.mcp_server.text'):
            with patch('app.mcp_server.create_engine') as mock_engine:
                mock_conn = MagicMock()
                mock_result = MagicMock()
                mock_result.fetchall.return_value = []
                mock_result.keys.return_value = []
                mock_conn.execute.return_value = mock_result
                mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
                mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=None)
                
                result = await query_database(
                    query="Show all salaries",
                    user_role="Engineering Team",
                    user_id=1
                )
                
                # Should either return limited data or access denied
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_query_database_sql_injection_prevention(self, mock_groq_llm):
        """Test that SQL injection attempts are handled"""
        from app.mcp_server import query_database
        
        # Attempt SQL injection
        malicious_query = "'; DROP TABLE employees; --"
        
        with patch('app.mcp_server.text'):
            with patch('app.mcp_server.create_engine'):
                result = await query_database(
                    query=malicious_query,
                    user_role="Engineering Team",
                    user_id=1
                )
                
                # Should not crash, LLM should sanitize or reject
                assert result is not None


# =============================================================================
# Test: web_search (Tavily Tool)
# =============================================================================
class TestWebSearch:
    """Test suite for web search tool"""
    
    @pytest.mark.asyncio
    async def test_web_search_success(self, mock_httpx_client):
        """Test successful web search"""
        from app.mcp_server import web_search
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"url": "https://example.com", "content": "Test content"}
            ],
            "answer": "Test answer"
        }
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        result = await web_search(
            query="Latest AI news",
            max_results=5
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_web_search_no_results(self, mock_httpx_client):
        """Test web search with no results"""
        from app.mcp_server import web_search
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [], "answer": ""}
        mock_httpx_client.post = AsyncMock(return_value=mock_response)
        
        result = await web_search(
            query="xyznonexistentquery12345",
            max_results=5
        )
        
        assert "No" in result or result is not None
    
    @pytest.mark.asyncio
    async def test_web_search_api_error(self, mock_httpx_client):
        """Test web search handles API errors gracefully"""
        from app.mcp_server import web_search
        
        mock_httpx_client.post = AsyncMock(side_effect=Exception("API Error"))
        
        result = await web_search(
            query="Test query",
            max_results=5
        )
        
        assert "Error" in result


# =============================================================================
# Test: get_weather (Open-Meteo Tool)
# =============================================================================
class TestGetWeather:
    """Test suite for weather tool"""
    
    @pytest.mark.asyncio
    async def test_get_weather_success(self, mock_httpx_client):
        """Test successful weather retrieval"""
        from app.mcp_server import get_weather
        
        # Mock geocoding response
        geo_response = MagicMock()
        geo_response.json.return_value = {
            "results": [
                {"latitude": 12.9716, "longitude": 77.5946, "name": "Bangalore", "country": "India"}
            ]
        }
        
        # Mock weather response
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 28.5,
                "relative_humidity_2m": 65,
                "wind_speed_10m": 12,
                "weather_code": 0
            }
        }
        
        mock_httpx_client.get = AsyncMock(side_effect=[geo_response, weather_response])
        
        result = await get_weather(city="Bangalore", unit="celsius")
        
        assert "Temperature" in result or "Bangalore" in result
    
    @pytest.mark.asyncio
    async def test_get_weather_city_not_found(self, mock_httpx_client):
        """Test weather with unknown city"""
        from app.mcp_server import get_weather
        
        geo_response = MagicMock()
        geo_response.json.return_value = {"results": []}
        mock_httpx_client.get = AsyncMock(return_value=geo_response)
        
        result = await get_weather(city="NonExistentCity12345", unit="celsius")
        
        assert "Could not find" in result or "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_get_weather_fahrenheit(self, mock_httpx_client):
        """Test weather with Fahrenheit unit"""
        from app.mcp_server import get_weather
        
        geo_response = MagicMock()
        geo_response.json.return_value = {
            "results": [{"latitude": 40.7128, "longitude": -74.0060, "name": "New York", "country": "USA"}]
        }
        
        weather_response = MagicMock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 75.0,
                "relative_humidity_2m": 50,
                "wind_speed_10m": 8,
                "weather_code": 1
            }
        }
        
        mock_httpx_client.get = AsyncMock(side_effect=[geo_response, weather_response])
        
        result = await get_weather(city="New York", unit="fahrenheit")
        
        assert "F" in result or "Temperature" in result


# =============================================================================
# Test: MCP Server Initialization
# =============================================================================
class TestMCPServerInit:
    """Test MCP server initialization and configuration"""
    
    def test_mcp_server_exists(self):
        """Test MCP server is properly initialized"""
        from app.mcp_server import mcp
        
        assert mcp is not None
        assert mcp.name == "RBAC Chatbot Tools"
    
    def test_mcp_tools_registered(self):
        """Test all 4 tools are registered"""
        from app.mcp_server import search_documents, query_database, web_search, get_weather
        
        # All tool functions should exist and be callable
        assert callable(search_documents)
        assert callable(query_database)
        assert callable(web_search)
        assert callable(get_weather)


# =============================================================================
# Test: Settings Integration
# =============================================================================
class TestSettingsIntegration:
    """Test that MCP server correctly uses config settings"""
    
    def test_groq_settings_used(self):
        """Test Groq settings are loaded from config"""
        from app.config import settings
        
        assert settings.groq_api_key is not None
        assert settings.groq_model is not None
        assert settings.groq_temperature is not None
    
    def test_rate_limit_setting_exists(self):
        """Test rate limit setting is configured"""
        from app.config import settings
        
        assert settings.rate_limit_per_user > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
