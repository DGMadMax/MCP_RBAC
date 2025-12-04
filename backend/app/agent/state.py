"""
Agent State - TypedDict for LangGraph
"""

from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict):
    """
    State schema for LangGraph agentic workflow
    """
    
    # User context
    user_id: int
    user_role: str
    user_department: str
    
    # Query processing
    original_query: str
    rewritten_queries: List[str]
    is_multi_query: bool
    
    # Chat history (last 4 messages)
    chat_history: List[Dict[str, str]]
    
    # Intent classification
    intent: str  # "greeting", "sql", "web", "weather", "rag", "multi_tool"
    tools_to_call: List[str]  # e.g., ["rag", "sql"]
    
    # Tool results
    rag_results: Optional[Dict[str, Any]]
    sql_results: Optional[Dict[str, Any]]
    web_results: Optional[Dict[str, Any]]
    weather_results: Optional[Dict[str, Any]]
    
    # Final output
    final_response: str
    sources: List[Dict[str, str]]
    confidence: str
    
    # Metadata (for SSE streaming)
    status_updates: List[str]
    current_stage: str
