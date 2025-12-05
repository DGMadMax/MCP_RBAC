"""
LangGraph Workflow - Agentic Chat with MCP Tools
Max iterations: 5
Memory: Conversation history persisted per session
"""

from typing import List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.agent.state import AgentState
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Maximum iterations before stopping
MAX_ITERATIONS = 5


# =============================================================================
# Node: Router - Classify intent and select tool
# =============================================================================
async def router_node(state: AgentState) -> AgentState:
    """
    Classify user intent and decide which tool to call.
    """
    from langchain_groq import ChatGroq
    
    query = state["original_query"]
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["current_status"] = "Analyzing your question..."
    
    logger.info(f"[ROUTER] Iteration {state['iteration_count']}/{MAX_ITERATIONS} | Query: {query[:50]}...")
    
    # Check iteration limit
    if state["iteration_count"] > MAX_ITERATIONS:
        state["intent"] = "max_reached"
        state["is_complete"] = True
        return state
    
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=settings.groq_temperature
    )
    
    # Build context from chat history
    history_context = ""
    messages = state.get("messages", [])
    if messages:
        recent = messages[-6:]  # Last 3 exchanges
        for msg in recent:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            history_context += f"{role}: {msg.content[:200]}\n"
    
    prompt = f"""Classify this user query into ONE of these categories:
- rag: Questions about internal documents, policies, company info
- sql: Questions about employee data, statistics, database queries
- web: Questions needing current web information, news, external data
- weather: Weather-related questions for any city
- greeting: Hello, hi, thanks, bye, etc.
- unknown: Cannot determine or out of scope

Recent conversation:
{history_context}

Current query: {query}

Respond with ONLY the category name (rag, sql, web, weather, greeting, or unknown).
"""
    
    response = await llm.ainvoke(prompt)
    intent = response.content.strip().lower()
    
    # Validate intent
    valid_intents = ["rag", "sql", "web", "weather", "greeting", "unknown"]
    if intent not in valid_intents:
        intent = "unknown"
    
    state["intent"] = intent
    state["selected_tool"] = intent if intent in ["rag", "sql", "web", "weather"] else None
    
    logger.info(f"[ROUTER] Intent: {intent}")
    
    return state


# =============================================================================
# Node: Tool Executor - Call the selected MCP tool
# =============================================================================
async def tool_executor_node(state: AgentState) -> AgentState:
    """
    Execute the selected tool via MCP.
    """
    from app.mcp_server import search_documents, query_database, web_search, get_weather
    
    tool = state.get("selected_tool")
    query = state.get("rewritten_query") or state["original_query"]
    
    state["current_status"] = f"Searching with {tool} tool..."
    
    logger.info(f"[TOOL] Executing: {tool}")
    
    try:
        if tool == "rag":
            state["current_status"] = "Searching documents..."
            result = await search_documents(
                query=query,
                department=state["user_department"],
                user_role=state["user_role"],
                top_k=3
            )
        elif tool == "sql":
            state["current_status"] = "Querying database..."
            result = await query_database(
                query=query,
                user_role=state["user_role"],
                user_id=state["user_id"]
            )
        elif tool == "web":
            state["current_status"] = "Searching the web..."
            result = await web_search(
                query=query,
                max_results=5
            )
        elif tool == "weather":
            # Use LLM to extract city from query
            from langchain_groq import ChatGroq
            
            extract_llm = ChatGroq(
                api_key=settings.groq_api_key,
                model_name=settings.groq_model,
                temperature=0
            )
            
            extract_prompt = f"""Extract ONLY the city name from this query. Return ONLY the city name, nothing else.

Query: {query}

City name:"""
            
            city_response = await extract_llm.ainvoke(extract_prompt)
            city = city_response.content.strip().replace('"', '').replace("'", "")
            
            # Fallback if extraction fails
            if not city or len(city) > 50 or city.lower() in ["unknown", "n/a", "none"]:
                city = "Mumbai"
            
            logger.info(f"[WEATHER] Extracted city: {city}")
            state["current_status"] = f"Getting weather for {city}..."
            result = await get_weather(city=city)
        else:
            result = None
        
        state["tool_result"] = result
        logger.info(f"[TOOL] Result length: {len(result) if result else 0}")
        
    except Exception as e:
        logger.error(f"[TOOL] Error: {str(e)}")
        state["tool_result"] = f"Error executing tool: {str(e)}"
    
    return state


# =============================================================================
# Node: Generator - Generate final response
# =============================================================================
async def generator_node(state: AgentState) -> AgentState:
    """
    Generate final response based on tool results or direct answer.
    """
    from langchain_groq import ChatGroq
    
    state["current_status"] = "Generating response..."
    
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=settings.groq_temperature
    )
    
    query = state["original_query"]
    intent = state["intent"]
    tool_result = state.get("tool_result")
    
    # Handle different intents
    if intent == "greeting":
        state["final_response"] = "Hello! I'm the RBAC Chatbot. I can help you with:\n- Searching company documents\n- Querying employee data\n- Web searches\n- Weather information\n\nHow can I assist you today?"
        state["is_complete"] = True
        state["needs_more_info"] = False
        return state
    
    if intent == "unknown" or (intent == "max_reached"):
        state["final_response"] = "I could not find an answer in the available documents or tools. Please try rephrasing your question or ask something related to company policies, employee data, web information, or weather."
        state["is_complete"] = True
        state["needs_more_info"] = False
        return state
    
    # Check if tool result is empty or error - generate fallback response
    if not tool_result or "Error" in str(tool_result) or "No relevant" in str(tool_result) or "No results" in str(tool_result):
        state["final_response"] = f"I could not find an answer for your question. The tool returned: {str(tool_result)[:200] if tool_result else 'no results'}. Please try rephrasing your question."
        state["is_complete"] = True
        state["needs_more_info"] = False
        return state
    
    # Generate response with context
    prompt = f"""Based on the following information, answer the user's question concisely and accurately.

User Question: {query}

Retrieved Information:
{tool_result[:3000]}

Instructions:
- Answer the question directly
- If the information doesn't fully answer the question, say so
- Be concise but complete
- Cite sources if available
"""
    
    response = await llm.ainvoke(prompt)
    state["final_response"] = response.content
    state["is_complete"] = True
    state["needs_more_info"] = False
    
    # Add AI message to history
    state["messages"].append(AIMessage(content=response.content))
    
    return state


# =============================================================================
# Routing Logic
# =============================================================================
def should_continue(state: AgentState) -> str:
    """
    Decide next step based on current state.
    """
    intent = state.get("intent", "unknown")
    is_complete = state.get("is_complete", False)
    needs_more = state.get("needs_more_info", False)
    iteration = state.get("iteration_count", 0)
    
    # If complete, go to end
    if is_complete:
        return "end"
    
    # If greeting or unknown, go straight to generator
    if intent in ["greeting", "unknown", "max_reached"]:
        return "generate"
    
    # If tool selected, execute it
    if state.get("selected_tool") and not state.get("tool_result"):
        return "execute"
    
    # If needs more info and under limit, route again
    if needs_more and iteration < MAX_ITERATIONS:
        return "route"
    
    # Default: generate
    return "generate"


# =============================================================================
# Build LangGraph Workflow
# =============================================================================
def create_agent_graph():
    """
    Create and compile the LangGraph workflow.
    
    Flow:
    1. Router -> Classify intent
    2. If tool needed -> Tool Executor -> Generator
    3. If greeting/unknown -> Generator
    4. Loop back if needs_more_info (max 5 iterations)
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("generator", generator_node)
    
    # Entry point
    workflow.set_entry_point("router")
    
    # Conditional routing after router
    workflow.add_conditional_edges(
        "router",
        should_continue,
        {
            "execute": "tool_executor",
            "generate": "generator",
            "route": "router",
            "end": END
        }
    )
    
    # After tool executor -> generator
    workflow.add_edge("tool_executor", "generator")
    
    # Conditional after generator
    workflow.add_conditional_edges(
        "generator",
        should_continue,
        {
            "route": "router",
            "end": END
        }
    )
    
    # Compile with memory
    memory = MemorySaver()
    graph = workflow.compile(
        checkpointer=memory
    )
    
    logger.info("[GRAPH] LangGraph workflow compiled successfully")
    
    return graph, memory


# =============================================================================
# Global agent instance
# =============================================================================
agent_graph, agent_memory = create_agent_graph()


# =============================================================================
# Helper function to run agent
# =============================================================================
async def run_agent(
    query: str,
    user_id: int,
    user_role: str,
    user_department: str,
    session_id: str,
    chat_history: List = None
):
    """
    Run the agent with the given query.
    
    Returns generator for SSE streaming.
    """
    from langchain_core.messages import HumanMessage
    
    # Build initial state
    initial_state = {
        "user_id": user_id,
        "user_role": user_role,
        "user_department": user_department,
        "session_id": session_id,
        "messages": chat_history or [],
        "original_query": query,
        "rewritten_query": query,
        "iteration_count": 0,
        "max_iterations": MAX_ITERATIONS,
        "intent": "",
        "selected_tool": None,
        "tool_result": None,
        "final_response": "",
        "sources": [],
        "current_status": "Starting...",
        "is_complete": False,
        "needs_more_info": False
    }
    
    # Add user message to history
    initial_state["messages"].append(HumanMessage(content=query))
    
    # Config with thread_id for memory
    config = {"configurable": {"thread_id": session_id}}
    
    # Run graph
    final_state = None
    async for event in agent_graph.astream(initial_state, config):
        # Yield status updates for SSE
        for node_name, node_state in event.items():
            status = node_state.get("current_status", "")
            if status:
                yield {"type": "status", "content": status}
        final_state = node_state
    
    # Yield final response
    if final_state:
        yield {
            "type": "response",
            "content": final_state.get("final_response", "I could not generate a response."),
            "sources": final_state.get("sources", [])
        }
