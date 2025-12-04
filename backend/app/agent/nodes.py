"""
LangGraph Agent Nodes - Workflow Components
Adapted from user's src/agent/ files
"""

import json
import asyncio
from typing import Dict, Any
from langchain_groq import ChatGroq

from app.agent.state import AgentState
from app.agent.prompts import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    QUERY_REWRITER_PROMPT,
    SYNTHESIS_PROMPT
)
from app.mcp_client import rag_client, sql_client, web_client, weather_client
from app.config import settings
from app.logger import get_logger, log_llm_response, log_chunks

logger = get_logger(__name__)

# Initialize Groq LLM
llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_model,
    temperature=settings.groq_temperature
)


# =============================================================================
# Node 1: Orchestrator (Intent Classification)
# =============================================================================
async def orchestrator_node(state: AgentState) -> AgentState:
    """
    Classify user intent and determine which tools to call
    Adapted from user's src/agent/orchestrator.py
    """
    query = state["original_query"]
    
    logger.info(f"[ORCHESTRATOR] Classifying intent for: {query[:100]}...")
    
    prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(query=query)
    
    try:
        response = await llm.ainvoke(prompt)
        result = json.loads(response.content)
        
        if settings.log_llm_responses:
            log_llm_response(logger, query, response.content, "orchestrator")
        
        state["intent"] = result["intent"]
        
        # If greeting/chit_chat, set direct response
        if state["intent"] in ["greeting", "chit_chat"]:
            state["final_response"] = result.get("response", "Hello! How can I help you today?")
            state["tools_to_call"] = []
        else:
            # Determine tools to call
            state["tools_to_call"] = result.get("tools", [state["intent"]])
        
        logger.info(f"[ORCHESTRATOR] Intent: {state['intent']} | Tools: {state['tools_to_call']}")
        state["current_stage"] = "query_rewriting"
        
        return state
        
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Failed: {str(e)}")
        # Fallback
        state["intent"] = "rag"
        state["tools_to_call"] = ["rag"]
        return state


# =============================================================================
# Node 2: Query Rewriter
# =============================================================================
async def query_rewriter_node(state: AgentState) -> AgentState:
    """
    Rewrite query for better retrieval
    Adapted from user's src/agent/query_rewriter.py
    """
    if state["intent"] in ["greeting", "chit_chat"]:
        return state  # Skip rewriting for greetings
    
    query = state["original_query"]
    
    logger.info(f"[QUERY_REWRITER] Rewriting query: {query[:100]}...")
    
    prompt = QUERY_REWRITER_PROMPT.format(query=query)
    
    try:
        response = await llm.ainvoke(prompt)
        result = json.loads(response.content)
        
        if settings.log_llm_responses:
            log_llm_response(logger, query, response.content, "query_rewriter")
        
        state["is_multi_query"] = result.get("is_multi_part", False)
        
        if state["is_multi_query"]:
            state["rewritten_queries"] = result.get("sub_queries", [query])
        else:
            state["rewritten_queries"] = [result.get("rewritten_query", query)]
        
        logger.info(f"[QUERY_REWRITER] Rewritten: {state['rewritten_queries']}")
        state["current_stage"] = "tool_execution"
        
        return state
        
    except Exception as e:
        logger.error(f"[QUERY_REWRITER] Failed: {str(e)}")
        # Fallback to original query
        state["is_multi_query"] = False
        state["rewritten_queries"] = [query]
        return state


# =============================================================================
# Node 3: Tool Executor (Parallel MCP Calls)
# =============================================================================
async def tool_executor_node(state: AgentState) -> AgentState:
    """
    Execute tools in parallel via MCP servers
    """
    tools = state["tools_to_call"]
    query = state["rewritten_queries"][0] if state["rewritten_queries"] else state["original_query"]
    
    logger.info(f"[TOOL_EXECUTOR] Executing tools: {tools}")
    
    # Prepare tool calls
    tasks = []
    
    if "rag" in tools:
        tasks.append(("rag", rag_client.search(
            query=query,
            user_department=state["user_department"],
            user_role=state["user_role"],
            user_id=state["user_id"],
            top_k=3
        )))
    
    if "sql" in tools:
        tasks.append(("sql", sql_client.query(
            query=query,
            user_role=state["user_role"],
            user_id=state["user_id"]
        )))
    
    if "web" in tools:
        tasks.append(("web", web_client.search(
            query=query,
            user_id=state["user_id"],
            recency_filter="month"
        )))
    
    if "weather" in tools:
        tasks.append(("weather", weather_client.get_weather(
            query=query,
            user_id=state["user_id"]
        )))
    
    # Execute in parallel
    results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
    
    # Store results
    for (tool_name, _), result in zip(tasks, results):
        if isinstance(result, Exception):
            logger.error(f"[TOOL_EXECUTOR] {tool_name} failed: {str(result)}")
            result_dict = None
        else:
            result_dict = result
        
        # Store in state
        if tool_name == "rag":
            state["rag_results"] = result_dict
            if result_dict and settings.log_rag_chunks:
                log_chunks(logger, result_dict.get("results", []), "RAG-FINAL")
        elif tool_name == "sql":
            state["sql_results"] = result_dict
        elif tool_name == "web":
            state["web_results"] = result_dict
        elif tool_name == "weather":
            state["weather_results"] = result_dict
    
    logger.info(f"[TOOL_EXECUTOR] Tools executed successfully")
    state["current_stage"] = "synthesis"
    
    return state


# =============================================================================
# Node 4: Response Synthesizer
# =============================================================================
async def synthesizer_node(state: AgentState) -> AgentState:
    """
    Synthesize final response from tool results
    """
    if state["final_response"]:
        # Already set by orchestrator (greeting/chit_chat)
        return state
    
    logger.info("[SYNTHESIZER] Generating final response...")
    
    # Build context from tool results
    context_parts = []
    sources = []
    
    # RAG results
    if state.get("rag_results") and state["rag_results"].get("success"):
        results = state["rag_results"].get("results", [])
        if results:
            context_parts.append("**Document Search Results**:")
            for i, doc in enumerate(results[:3], 1):
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})
                context_parts.append(f"\n{i}. {text}")
                
                # Add source
                sources.append({
                    "type": "document",
                    "file": metadata.get("file_name", "Unknown"),
                    "department": metadata.get("department", "general")
                })
    
    # SQL results
    if state.get("sql_results") and state["sql_results"].get("success"):
        sql_result = state["sql_results"].get("result", "")
        if sql_result:
            context_parts.append("\n\n**Database Query Results**:")
            context_parts.append(f"\n{sql_result}")
            sources.append({"type": "database", "table": "employees"})
    
    # Web results
    if state.get("web_results") and state["web_results"].get("success"):
        web_answer = state["web_results"].get("answer", "")
        web_sources = state["web_results"].get("sources", [])
        if web_answer:
            context_parts.append("\n\n**Web Search Results**:")
            context_parts.append(f"\n{web_answer}")
            for src in web_sources[:3]:
                sources.append({"type": "web", "url": src})
    
    # Weather results
    if state.get("weather_results") and state["weather_results"].get("success"):
        weather_formatted = state["weather_results"].get("formatted", "")
        if weather_formatted:
            context_parts.append("\n\n**Weather Information**:")
            context_parts.append(f"\n{weather_formatted}")
            sources.append({"type": "weather", "api": "Open-Meteo"})
    
    context = "\n".join(context_parts) if context_parts else "No relevant information found."
    
    # Format chat history
    history_text = ""
    if state.get("chat_history"):
        history_text = "\n".join([
            f"User: {msg['query']}\nAssistant: {msg['response']}"
            for msg in state["chat_history"][-4:]  # Last 4 messages
        ])
    
    # Generate response
    prompt = SYNTHESIS_PROMPT.format(
        context=context,
        history=history_text,
        query=state["original_query"]
    )
    
    try:
        response = await llm.ainvoke(prompt)
        final_answer = response.content
        
        if settings.log_llm_responses:
            log_llm_response(logger, state["original_query"], final_answer, "synthesizer")
        
        state["final_response"] = final_answer
        state["sources"] = sources
        state["confidence"] = "high" if len(sources) > 0 else "low"
        
        logger.info("[SYNTHESIZER] Response generated successfully")
        state["current_stage"] = "complete"
        
        return state
        
    except Exception as e:
        logger.error(f"[SYNTHESIZER] Failed: {str(e)}")
        state["final_response"] = "I apologize, but I encountered an error generating a response."
        state["sources"] = []
        state["confidence"] = "low"
        return state
