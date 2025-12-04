"""
Unit Tests for LangGraph Agent Nodes
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.agent.state import AgentState


class TestOrchestratorNode:
    """Test Orchestrator Node (Intent Classification)"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_greeting_intent(self):
        """Test orchestrator classifies greeting correctly"""
        from app.agent.nodes import orchestrator_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "Hello!",
            "rewritten_queries": [],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "",
            "tools_to_call": [],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = '{"intent": "greeting", "response": "Hello! How can I help you?"}'
        
        with patch("app.agent.nodes.llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)
            
            result = await orchestrator_node(state)
            
            assert result["intent"] == "greeting"
            assert result["final_response"] == "Hello! How can I help you?"
            assert len(result["tools_to_call"]) == 0
    
    @pytest.mark.asyncio
    async def test_orchestrator_rag_intent(self):
        """Test orchestrator routes to RAG"""
        from app.agent.nodes import orchestrator_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "What is our system architecture?",
            "rewritten_queries": [],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "",
            "tools_to_call": [],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        mock_llm_response = Mock()
        mock_llm_response.content = '{"intent": "rag", "tools": ["rag"]}'
        
        with patch("app.agent.nodes.llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)
            
            result = await orchestrator_node(state)
            
            assert result["intent"] == "rag"
            assert "rag" in result["tools_to_call"]
            assert result["final_response"] == ""


class TestQueryRewriterNode:
    """Test Query Rewriter Node"""
    
    @pytest.mark.asyncio
    async def test_query_rewriter_single_query(self):
        """Test query rewriter with single query"""
        from app.agent.nodes import query_rewriter_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "umm like what is the architecture you know",
            "rewritten_queries": [],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "rag",
            "tools_to_call": ["rag"],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        mock_llm_response = Mock()
        mock_llm_response.content = '{"is_multi_part": false, "rewritten_query": "What is the architecture?"}'
        
        with patch("app.agent.nodes.llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)
            
            result = await query_rewriter_node(state)
            
            assert result["is_multi_query"] is False
            assert result["rewritten_queries"] == ["What is the architecture?"]
    
    @pytest.mark.asyncio
    async def test_query_rewriter_multi_query(self):
        """Test query rewriter splits multi-part query"""
        from app.agent.nodes import query_rewriter_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "What is the weather in Bangalore and show me HR policies",
            "rewritten_queries": [],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "multi_tool",
            "tools_to_call": ["weather", "rag"],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        mock_llm_response = Mock()
        mock_llm_response.content = '''{
            "is_multi_part": true,
            "sub_queries": ["What is the weather in Bangalore?", "Show me HR policies"]
        }'''
        
        with patch("app.agent.nodes.llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)
            
            result = await query_rewriter_node(state)
            
            assert result["is_multi_query"] is True
            assert len(result["rewritten_queries"]) == 2


class TestToolExecutorNode:
    """Test Tool Executor Node"""
    
    @pytest.mark.asyncio
    async def test_tool_executor_rag_only(self, mock_rag_results):
        """Test tool executor with RAG tool only"""
        from app.agent.nodes import tool_executor_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "What is the architecture?",
            "rewritten_queries": ["What is the architecture?"],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "rag",
            "tools_to_call": ["rag"],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        with patch("app.agent.nodes.rag_client") as mock_rag:
            mock_rag.search = AsyncMock(return_value=mock_rag_results)
            
            result = await tool_executor_node(state)
            
            assert result["rag_results"] is not None
            assert result["rag_results"]["success"] is True
            assert mock_rag.search.called
    
    @pytest.mark.asyncio
    async def test_tool_executor_parallel_execution(self, mock_rag_results, mock_web_results):
        """Test parallel execution of multiple tools"""
        from app.agent.nodes import tool_executor_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "Search company docs and web",
            "rewritten_queries": ["Search company docs and web"],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "multi_tool",
            "tools_to_call": ["rag", "web"],
            "rag_results": None,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        with patch("app.agent.nodes.rag_client") as mock_rag, \
             patch("app.agent.nodes.web_client") as mock_web:
            
            mock_rag.search = AsyncMock(return_value=mock_rag_results)
            mock_web.search = AsyncMock(return_value=mock_web_results)
            
            result = await tool_executor_node(state)
            
            assert result["rag_results"] is not None
            assert result["web_results"] is not None
            assert mock_rag.search.called
            assert mock_web.search.called


class TestSynthesizerNode:
    """Test Response Synthesizer Node"""
    
    @pytest.mark.asyncio
    async def test_synthesizer_with_rag_results(self, mock_rag_results):
        """Test synthesizer combines RAG results"""
        from app.agent.nodes import synthesizer_node
        
        state: AgentState = {
            "user_id": 1,
            "user_role": "Engineering Team",
            "user_department": "engineering",
            "original_query": "What is the architecture?",
            "rewritten_queries": ["What is the architecture?"],
            "is_multi_query": False,
            "chat_history": [],
            "intent": "rag",
            "tools_to_call": ["rag"],
            "rag_results": mock_rag_results,
            "sql_results": None,
            "web_results": None,
            "weather_results": None,
            "final_response": "",
            "sources": [],
            "confidence": "",
            "status_updates": [],
            "current_stage": ""
        }
        
        mock_llm_response = Mock()
        mock_llm_response.content = "FinSolve uses microservices architecture with Python and FastAPI."
        
        with patch("app.agent.nodes.llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)
            
            result = await synthesizer_node(state)
            
            assert result["final_response"] != ""
            assert len(result["sources"]) > 0
            assert result["confidence"] == "high"
