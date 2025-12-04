"""
LangGraph Workflow - Agentic Chat Graph
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes import (
    orchestrator_node,
    query_rewriter_node,
    tool_executor_node,
    synthesizer_node
)
from app.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Routing Logic
# =============================================================================
def should_execute_tools(state: AgentState) -> str:
    """
    Decide whether to execute tools or skip to synthesis
    
    Returns:
        "execute_tools" if tools needed, "synthesize" if not
    """
    if state["intent"] in ["greeting", "chit_chat"]:
        return "synthesize"
    return "execute_tools"


# =============================================================================
# Build LangGraph Workflow
# =============================================================================
def create_agent_graph():
    """
    Create and compile the LangGraph workflow
    
    Flow:
    1. Orchestrator (classify intent)
    2. Query Rewriter (clean up query)
    3. Router:
        - If greeting/chit_chat → Synthesizer
        - Else → Tool Executor
    4. Tool Executor (parallel MCP calls)
    5. Synthesizer (generate final response)
    """
    # Initialize workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("query_rewriter", query_rewriter_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # Define edges
    workflow.set_entry_point("orchestrator")
    
    # After orchestrator → query rewriter
    workflow.add_edge("orchestrator", "query_rewriter")
    
    # After query rewriter → conditional routing
    workflow.add_conditional_edges(
        "query_rewriter",
        should_execute_tools,
        {
            "execute_tools": "tool_executor",
            "synthesize": "synthesizer"
        }
    )
    
    # After tool executor → synthesizer
    workflow.add_edge("tool_executor", "synthesizer")
    
    # After synthesizer → END
    workflow.add_edge("synthesizer", END)
    
    # Compile with memory
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    logger.info("✅ LangGraph workflow compiled successfully")
    
    return graph, memory


# =============================================================================
# Global agent instance
# =============================================================================
agent_graph, agent_memory = create_agent_graph()
