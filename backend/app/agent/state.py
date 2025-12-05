"""
Agent State - TypedDict for LangGraph
"""

from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State schema for LangGraph agentic workflow
    """
    
    # User context
    user_id: int
    user_role: str
    user_department: str
    session_id: str
    
    # Messages (with memory - using add_messages reducer)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Current query
    original_query: str
    rewritten_query: str
    
    # Iteration control
    iteration_count: int
    max_iterations: int  # Default: 5
    
    # Intent classification
    intent: str  # "greeting", "sql", "web", "weather", "rag", "unknown"
    selected_tool: Optional[str]  # Which tool to call
    
    # Tool results
    tool_result: Optional[str]
    
    # Final output
    final_response: str
    sources: List[Dict[str, str]]
    
    # Status for SSE streaming
    current_status: str
    is_complete: bool
    needs_more_info: bool
