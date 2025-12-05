"""
Unit Tests for LangGraph Agent
Production-Grade Test Suite for RBAC Agentic AI Chatbot

Tests cover:
- Router node (intent classification)
- Tool executor node
- Generator node (response synthesis)
- Agent graph compilation
- Memory and iteration limits

Author: Senior Software Engineer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def sample_agent_state():
    """Create a sample agent state for testing"""
    return {
        "user_id": 1,
        "user_role": "Engineering Team",
        "user_department": "engineering",
        "original_query": "What are the engineering policies?",
        "rewritten_query": None,
        "session_id": "test_session_123",
        "messages": [HumanMessage(content="What are the engineering policies?")],
        "intent": None,
        "selected_tool": None,
        "tool_result": None,
        "final_response": None,
        "sources": [],
        "is_complete": False,
        "needs_more_info": False,
        "iteration_count": 0,
        "current_status": ""
    }


@pytest.fixture
def mock_groq_llm():
    """Mock Groq LLM for all tests"""
    with patch('app.agent.graph.ChatGroq') as mock:
        llm = MagicMock()
        mock.return_value = llm
        yield llm


# =============================================================================
# Test: Router Node
# =============================================================================
class TestRouterNode:
    """Test suite for intent classification router"""
    
    @pytest.mark.asyncio
    async def test_router_classifies_greeting(self, sample_agent_state, mock_groq_llm):
        """Test router correctly identifies greeting intent"""
        from app.agent.graph import router_node
        
        sample_agent_state["original_query"] = "Hello, how are you?"
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(content="greeting"))
        
        result = await router_node(sample_agent_state)
        
        assert result["intent"] == "greeting"
        assert result["iteration_count"] == 1
    
    @pytest.mark.asyncio
    async def test_router_classifies_rag(self, sample_agent_state, mock_groq_llm):
        """Test router correctly identifies RAG intent"""
        from app.agent.graph import router_node
        
        sample_agent_state["original_query"] = "What are the company policies?"
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(content="rag"))
        
        result = await router_node(sample_agent_state)
        
        assert result["intent"] == "rag"
        assert result["selected_tool"] == "rag"
    
    @pytest.mark.asyncio
    async def test_router_classifies_sql(self, sample_agent_state, mock_groq_llm):
        """Test router correctly identifies SQL intent"""
        from app.agent.graph import router_node
        
        sample_agent_state["original_query"] = "How many employees work here?"
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(content="sql"))
        
        result = await router_node(sample_agent_state)
        
        assert result["intent"] == "sql"
        assert result["selected_tool"] == "sql"
    
    @pytest.mark.asyncio
    async def test_router_classifies_web(self, sample_agent_state, mock_groq_llm):
        """Test router correctly identifies web search intent"""
        from app.agent.graph import router_node
        
        sample_agent_state["original_query"] = "What is the latest news about AI?"
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(content="web"))
        
        result = await router_node(sample_agent_state)
        
        assert result["intent"] == "web"
        assert result["selected_tool"] == "web"
    
    @pytest.mark.asyncio
    async def test_router_classifies_weather(self, sample_agent_state, mock_groq_llm):
        """Test router correctly identifies weather intent"""
        from app.agent.graph import router_node
        
        sample_agent_state["original_query"] = "What's the weather in Mumbai?"
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(content="weather"))
        
        result = await router_node(sample_agent_state)
        
        assert result["intent"] == "weather"
        assert result["selected_tool"] == "weather"
    
    @pytest.mark.asyncio
    async def test_router_max_iterations(self, sample_agent_state, mock_groq_llm):
        """Test router stops at max iterations"""
        from app.agent.graph import router_node, MAX_ITERATIONS
        
        sample_agent_state["iteration_count"] = MAX_ITERATIONS
        
        result = await router_node(sample_agent_state)
        
        assert result["intent"] == "max_reached"
        assert result["is_complete"] == True


# =============================================================================
# Test: Tool Executor Node
# =============================================================================
class TestToolExecutorNode:
    """Test suite for tool execution node"""
    
    @pytest.mark.asyncio
    async def test_executor_calls_rag_tool(self, sample_agent_state):
        """Test executor correctly calls RAG tool"""
        from app.agent.graph import tool_executor_node
        
        sample_agent_state["selected_tool"] = "rag"
        sample_agent_state["intent"] = "rag"
        
        with patch('app.agent.graph.search_documents', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = "Found: Engineering policy document"
            
            result = await tool_executor_node(sample_agent_state)
            
            assert result["tool_result"] is not None
            mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_executor_calls_sql_tool(self, sample_agent_state):
        """Test executor correctly calls SQL tool"""
        from app.agent.graph import tool_executor_node
        
        sample_agent_state["selected_tool"] = "sql"
        sample_agent_state["intent"] = "sql"
        sample_agent_state["original_query"] = "Show all employees"
        
        with patch('app.agent.graph.query_database', new_callable=AsyncMock) as mock_sql:
            mock_sql.return_value = "Found 10 employees"
            
            result = await tool_executor_node(sample_agent_state)
            
            assert result["tool_result"] is not None
            mock_sql.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_executor_handles_tool_error(self, sample_agent_state):
        """Test executor handles tool errors gracefully"""
        from app.agent.graph import tool_executor_node
        
        sample_agent_state["selected_tool"] = "rag"
        sample_agent_state["intent"] = "rag"
        
        with patch('app.agent.graph.search_documents', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = Exception("Tool failed")
            
            result = await tool_executor_node(sample_agent_state)
            
            assert "Error" in result["tool_result"]
    
    @pytest.mark.asyncio
    async def test_executor_weather_city_extraction(self, sample_agent_state, mock_groq_llm):
        """Test weather tool extracts city correctly using LLM"""
        from app.agent.graph import tool_executor_node
        
        sample_agent_state["selected_tool"] = "weather"
        sample_agent_state["intent"] = "weather"
        sample_agent_state["original_query"] = "What's the weather in Bangalore?"
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Bangalore"))
        
        with patch('app.agent.graph.get_weather', new_callable=AsyncMock) as mock_weather:
            mock_weather.return_value = "Weather in Bangalore: 28°C"
            
            result = await tool_executor_node(sample_agent_state)
            
            assert result["tool_result"] is not None


# =============================================================================
# Test: Generator Node
# =============================================================================
class TestGeneratorNode:
    """Test suite for response generation node"""
    
    @pytest.mark.asyncio
    async def test_generator_greeting_response(self, sample_agent_state):
        """Test generator returns greeting for greeting intent"""
        from app.agent.graph import generator_node
        
        sample_agent_state["intent"] = "greeting"
        
        result = await generator_node(sample_agent_state)
        
        assert "Hello" in result["final_response"]
        assert result["is_complete"] == True
    
    @pytest.mark.asyncio
    async def test_generator_with_tool_result(self, sample_agent_state, mock_groq_llm):
        """Test generator synthesizes response from tool result"""
        from app.agent.graph import generator_node
        
        sample_agent_state["intent"] = "rag"
        sample_agent_state["tool_result"] = "Engineering policies require code reviews."
        
        mock_groq_llm.ainvoke = AsyncMock(return_value=MagicMock(
            content="Based on the policies, code reviews are required."
        ))
        
        result = await generator_node(sample_agent_state)
        
        assert result["final_response"] is not None
        assert result["is_complete"] == True
    
    @pytest.mark.asyncio
    async def test_generator_handles_empty_result(self, sample_agent_state):
        """Test generator handles empty tool results"""
        from app.agent.graph import generator_node
        
        sample_agent_state["intent"] = "rag"
        sample_agent_state["tool_result"] = ""
        
        result = await generator_node(sample_agent_state)
        
        assert "could not find" in result["final_response"].lower()
        assert result["is_complete"] == True
    
    @pytest.mark.asyncio
    async def test_generator_handles_error_result(self, sample_agent_state):
        """Test generator handles error in tool results"""
        from app.agent.graph import generator_node
        
        sample_agent_state["intent"] = "sql"
        sample_agent_state["tool_result"] = "Error: Database connection failed"
        
        result = await generator_node(sample_agent_state)
        
        assert result["is_complete"] == True
        assert result["needs_more_info"] == False


# =============================================================================
# Test: Agent Graph
# =============================================================================
class TestAgentGraph:
    """Test suite for complete agent graph"""
    
    def test_graph_compiles(self):
        """Test agent graph compiles without errors"""
        from app.agent.graph import agent_graph
        
        assert agent_graph is not None
    
    def test_graph_has_memory(self):
        """Test agent graph has memory checkpointer"""
        from app.agent.graph import agent_memory
        
        assert agent_memory is not None
    
    def test_max_iterations_constant(self):
        """Test MAX_ITERATIONS is properly set"""
        from app.agent.graph import MAX_ITERATIONS
        
        assert MAX_ITERATIONS == 5
    
    @pytest.mark.asyncio
    async def test_run_agent_function_exists(self):
        """Test run_agent async generator function exists"""
        from app.agent.graph import run_agent
        
        assert callable(run_agent)


# =============================================================================
# Test: State Schema
# =============================================================================
class TestAgentState:
    """Test agent state schema"""
    
    def test_agent_state_import(self):
        """Test AgentState can be imported"""
        from app.agent.state import AgentState
        
        assert AgentState is not None
    
    def test_state_required_fields(self):
        """Test AgentState has all required fields"""
        from app.agent.state import AgentState
        
        required_fields = [
            "user_id", "user_role", "user_department",
            "original_query", "session_id", "messages",
            "intent", "selected_tool", "tool_result",
            "final_response", "is_complete", "iteration_count"
        ]
        
        # AgentState is a TypedDict, check annotations
        for field in required_fields:
            assert field in AgentState.__annotations__


# =============================================================================
# Test: Conditional Routing
# =============================================================================
class TestConditionalRouting:
    """Test conditional edge functions"""
    
    def test_should_continue_to_tool(self, sample_agent_state):
        """Test routing to tool executor"""
        from app.agent.graph import should_continue
        
        sample_agent_state["intent"] = "rag"
        sample_agent_state["is_complete"] = False
        sample_agent_state["tool_result"] = None
        
        result = should_continue(sample_agent_state)
        
        assert result == "tool_executor"
    
    def test_should_continue_to_generator(self, sample_agent_state):
        """Test routing to generator after tool execution"""
        from app.agent.graph import should_continue
        
        sample_agent_state["intent"] = "rag"
        sample_agent_state["is_complete"] = False
        sample_agent_state["tool_result"] = "Some result"
        
        result = should_continue(sample_agent_state)
        
        assert result == "generator"
    
    def test_should_continue_to_end(self, sample_agent_state):
        """Test routing to end when complete"""
        from app.agent.graph import should_continue
        
        sample_agent_state["is_complete"] = True
        
        result = should_continue(sample_agent_state)
        
        assert result == "end"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
