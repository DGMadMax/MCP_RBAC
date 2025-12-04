"""
LangGraph agent for orchestrating multiple tools.
"""
from typing import Dict, Any, List
import asyncio

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from config import settings
from logger import log_info, log_error
from mcp_servers.rag_server import rag_search
from mcp_servers.sql_server import sql_query
from mcp_servers.web_server import web_search
from mcp_servers.weather_server import weather_query
from metrics import tool_calls_total


class AgentState(BaseModel):
    """State for agent execution."""
    query: str
    user_department: str
    allowed_departments: List[str]
    
    # Tool decisions
    tools_to_call: List[str] = []
    
    # Tool results
    rag_results: List[Dict] = []
    sql_results: str = ""
    web_results: str = ""
    weather_results: str = ""
    
    # Final output
    response: str = ""
    sources: List[Dict] = []
    tools_used: List[str] = []


class AgentService:
    """Agent service for query processing."""
    
    def __init__(self, user_department: str, allowed_departments: List[str]):
        self.user_department = user_department
        self.allowed_departments = allowed_departments
        
        # Initialize LLM
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
    
    async def classify_query(self, state: AgentState) -> AgentState:
        """
        Classify query and decide which tools to use.
        """
        log_info("Classifying query", query=state.query[:100])
        
        classification_prompt = f"""
Analyze this query and determine which tools to use:

Query: {state.query}

Available tools:
1. rag_search - Search internal company documents (policies, reports, technical docs)
2. sql_query - Query structured employee/project data
3. web_search - Search the internet for latest information
4. weather - Get weather data for a city

Respond with ONLY a JSON object with a "tools" array:
{{"tools": ["rag_search", "sql_query"]}}

If no tools needed, return: {{"tools": []}}
"""
        
        try:
            response = await self.llm.ainvoke(classification_prompt)
            import json
            decision = json.loads(response.content)
            state.tools_to_call = decision.get("tools", [])
            
            log_info("Tools selected", tools=state.tools_to_call)
            
        except Exception as e:
            log_error("Query classification failed", exc_info=True)
            # Default to RAG search
            state.tools_to_call = ["rag_search"]
        
        return state
    
    async def execute_rag_tool(self, state: AgentState) -> AgentState:
        """Execute RAG search."""
        if "rag_search" not in state.tools_to_call:
            return state
        
        log_info("Executing RAG tool")
        
        try:
            results = await rag_search(
                query=state.query,
                department=self.user_department,
                top_k=settings.TOP_K_RERANK
            )
            
            state.rag_results = results
            state.tools_used.append("rag_search")
            
            tool_calls_total.labels(tool="rag", status="success").inc()
            log_info("RAG tool completed", results_count=len(results))
        
        except Exception as e:
            log_error("RAG tool failed", exc_info=True)
            tool_calls_total.labels(tool="rag", status="failure").inc()
        
        return state
    
    async def execute_sql_tool(self, state: AgentState) -> AgentState:
        """Execute SQL query."""
        if "sql_query" not in state.tools_to_call:
            return state
        
        log_info("Executing SQL tool")
        
        try:
            result = await sql_query(state.query)
            state.sql_results = result
            state.tools_used.append("sql_query")
            
            tool_calls_total.labels(tool="sql", status="success").inc()
            log_info("SQL tool completed")
        
        except Exception as e:
            log_error("SQL tool failed", exc_info=True)
            tool_calls_total.labels(tool="sql", status="failure").inc()
        
        return state
    
    async def execute_web_tool(self, state: AgentState) -> AgentState:
        """Execute web search."""
        if "web_search" not in state.tools_to_call:
            return state
        
        log_info("Executing web search tool")
        
        try:
            result = await web_search(state.query)
            state.web_results = result
            state.tools_used.append("web_search")
            
            tool_calls_total.labels(tool="web", status="success").inc()
            log_info("Web search completed")
        
        except Exception as e:
            log_error("Web search failed", exc_info=True)
            tool_calls_total.labels(tool="web", status="failure").inc()
        
        return state
    
    async def execute_weather_tool(self, state: AgentState) -> AgentState:
        """Execute weather query."""
        if "weather" not in state.tools_to_call:
            return state
        
        log_info("Executing weather tool")
        
        try:
            result = await weather_query(state.query)
            state.weather_results = result
            state.tools_used.append("weather")
            
            tool_calls_total.labels(tool="weather", status="success").inc()
            log_info("Weather tool completed")
        
        except Exception as e:
            log_error("Weather tool failed", exc_info=True)
            tool_calls_total.labels(tool="weather", status="failure").inc()
        
        return state
    
    async def synthesize_response(self, state: AgentState) -> AgentState:
        """Synthesize final response from all tool results."""
        log_info("Synthesizing response")
        
        # Build context from tool results
        context_parts = []
        
        if state.rag_results:
            rag_context = "\n\n".join([
                f"Document {i+1}: {doc['document'][:500]}"
                for i, doc in enumerate(state.rag_results)
            ])
            context_parts.append(f"Internal Documents:\n{rag_context}")
            state.sources = [
                {"type": "document", "content": doc["document"][:200], "metadata": doc.get("metadata", {})}
                for doc in state.rag_results
            ]
        
        if state.sql_results:
            context_parts.append(f"Database Query Results:\n{state.sql_results}")
        
        if state.web_results:
            context_parts.append(f"Web Search Results:\n{state.web_results}")
        
        if state.weather_results:
            context_parts.append(f"Weather Data:\n{state.weather_results}")
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No additional context available."
        
        synthesis_prompt = f"""
Based on the following information, provide a comprehensive answer to the user's question.

Question: {state.query}

Available Information:
{context}

Instructions:
- Provide a clear, concise answer
- Cite specific sources when possible
- If information is incomplete, acknowledge it
- Be professional and helpful

Answer:
"""
        
        try:
            response = await self.llm.ainvoke(synthesis_prompt)
            state.response = response.content
            
            log_info("Response synthesized")
        
        except Exception as e:
            log_error("Response synthesis failed", exc_info=True)
            state.response = "I apologize, but I encountered an error processing your request."
        
        return state
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute complete query processing pipeline.
        
        Args:
            query: User query string
            
        Returns:
            Dict with response, sources, and tools_used
        """
        log_info("Starting query execution", query=query[:100])
        
        # Initialize state
        state = AgentState(
            query=query,
            user_department=self.user_department,
            allowed_departments=self.allowed_departments
        )
        
        # Step 1: Classify query
        state = await self.classify_query(state)
        
        # Step 2: Execute tools in parallel
        tool_tasks = [
            self.execute_rag_tool(state),
            self.execute_sql_tool(state),
            self.execute_web_tool(state),
            self.execute_weather_tool(state)
        ]
        
        results = await asyncio.gather(*tool_tasks, return_exceptions=True)
        
        # Merge results (take first non-exception result for each tool)
        for result in results:
            if isinstance(result, AgentState):
                state = result
        
        # Step 3: Synthesize response
        state = await self.synthesize_response(state)
        
        log_info("Query execution completed", tools_used=state.tools_used)
        
        return {
            "response": state.response,
            "sources": state.sources,
            "tools_used": state.tools_used
        }
