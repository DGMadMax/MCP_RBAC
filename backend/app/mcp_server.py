"""
MCP Server - RBAC Chatbot Tools
Single MCP server with 4 async tools: RAG, SQL, Web Search, Weather
Uses official MCP library with @mcp.tool() decorators
"""

from mcp.server.fastmcp import FastMCP
from typing import Optional
import httpx
import asyncio

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Initialize MCP Server
mcp = FastMCP(
    name="RBAC Chatbot Tools",
    instructions="Tools for searching documents, querying databases, web search, and weather."
)


# =============================================================================
# Tool 1: RAG Search (Hybrid: Vector + BM25 + Reranker)
# =============================================================================
@mcp.tool()
async def search_documents(
    query: str,
    department: str,
    user_role: str,
    top_k: int = 3
) -> str:
    """
    Search internal documents using hybrid RAG pipeline with RBAC filtering.
    
    Args:
        query: The search query
        department: User's department for RBAC filtering (engineering, finance, hr, marketing, general)
        user_role: User's role for access control
        top_k: Number of results to return
    
    Returns:
        Relevant document chunks with sources
    """
    try:
        from app.rag.pipeline import hybrid_rag_search
        
        logger.info(f"[RAG] Searching for: {query[:50]}... | Dept: {department}")
        
        # Run sync function in executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: hybrid_rag_search(
                query=query,
                user_department=department,
                user_role=user_role,
                top_k=top_k
            )
        )
        
        if not results or len(results) == 0:
            return "No relevant documents found for this query."
        
        # Format results
        formatted = []
        for i, chunk in enumerate(results, 1):
            source = chunk.get("source", "Unknown")
            content = chunk.get("content", "")
            score = chunk.get("score", 0)
            formatted.append(f"[Source {i}: {source}] (Score: {score:.2f})\n{content}")
        
        return "\n\n---\n\n".join(formatted)
        
    except Exception as e:
        logger.error(f"[RAG] Search failed: {str(e)}")
        return f"Error searching documents: {str(e)}"


# =============================================================================
# Tool 2: SQL Query (Text-to-SQL with RBAC)
# =============================================================================
@mcp.tool()
async def query_database(
    query: str,
    user_role: str,
    user_id: int
) -> str:
    """
    Query the SQL database using natural language. Converts to SQL with RBAC filtering.
    
    Args:
        query: Natural language query about employee data
        user_role: User's role for access control
        user_id: User's ID for row-level security
    
    Returns:
        Query results as formatted text
    """
    try:
        from langchain_groq import ChatGroq
        from sqlalchemy import text
        from app.database import SessionLocal
        
        logger.info(f"[SQL] Query: {query[:50]}... | Role: {user_role}")
        
        # Define allowed tables based on role
        role_tables = {
            "admin": ["employees", "departments", "salaries", "performance"],
            "hr": ["employees", "departments"],
            "engineering": ["employees", "departments"],
            "finance": ["employees", "salaries"],
            "marketing": ["employees", "departments"],
        }
        
        allowed_tables = role_tables.get(user_role.lower(), ["employees"])
        
        # Generate SQL using LLM
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=settings.groq_temperature
        )
        
        prompt = f"""Convert this natural language query to SQL.
Only use these tables: {', '.join(allowed_tables)}
Query: {query}

Return ONLY the SQL query, nothing else. Use SQLite syntax.
If the query cannot be answered with available tables, return: SELECT 'Access denied or table not available' as error;
"""
        
        # Async LLM call
        sql_response = await llm.ainvoke(prompt)
        sql_query = sql_response.content.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```"):
            sql_query = sql_query.split("\n", 1)[1]
            sql_query = sql_query.rsplit("```", 1)[0]
        
        logger.info(f"[SQL] Generated: {sql_query[:100]}")
        
        # Execute query in executor (sync DB call)
        loop = asyncio.get_event_loop()
        
        def execute_query():
            db = SessionLocal()
            try:
                result = db.execute(text(sql_query))
                rows = result.fetchall()
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                return rows, columns
            finally:
                db.close()
        
        rows, columns = await loop.run_in_executor(None, execute_query)
        
        if not rows:
            return "Query returned no results."
        
        # Format as table
        output = f"Query: {sql_query}\n\nResults ({len(rows)} rows):\n"
        if columns:
            output += " | ".join(str(c) for c in columns) + "\n"
            output += "-" * 50 + "\n"
        
        for row in rows[:20]:  # Limit to 20 rows
            output += " | ".join(str(v) for v in row) + "\n"
        
        if len(rows) > 20:
            output += f"\n... and {len(rows) - 20} more rows"
        
        return output
        
    except Exception as e:
        logger.error(f"[SQL] Query failed: {str(e)}")
        return f"Error querying database: {str(e)}"


# =============================================================================
# Tool 3: Web Search (Tavily)
# =============================================================================
@mcp.tool()
async def web_search(
    query: str,
    max_results: int = 5
) -> str:
    """
    Search the web for current information using Tavily API.
    
    Args:
        query: Search query for web search
        max_results: Maximum number of results to return
    
    Returns:
        Web search results with sources
    """
    try:
        import os
        
        logger.info(f"[WEB] Searching: {query[:50]}...")
        
        # Use httpx async client for Tavily API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": True
                },
                timeout=30.0
            )
            
            data = response.json()
            
            if "error" in data:
                return f"Search error: {data['error']}"
            
            results = data.get("results", [])
            answer = data.get("answer", "")
            
            if not results and not answer:
                return "No web search results found."
            
            # Format results
            formatted = []
            if answer:
                formatted.append(f"Summary: {answer}\n")
            
            for i, result in enumerate(results, 1):
                url = result.get("url", "")
                content = result.get("content", "")[:500]
                formatted.append(f"[{i}] {url}\n{content}")
            
            return "\n\n".join(formatted)
        
    except Exception as e:
        logger.error(f"[WEB] Search failed: {str(e)}")
        return f"Error searching web: {str(e)}"


# =============================================================================
# Tool 4: Weather (Open-Meteo)
# =============================================================================
@mcp.tool()
async def get_weather(
    city: str,
    unit: str = "celsius"
) -> str:
    """
    Get current weather for a city using Open-Meteo API (free, no key required).
    
    Args:
        city: City name to get weather for
        unit: Temperature unit - 'celsius' or 'fahrenheit'
    
    Returns:
        Current weather information
    """
    try:
        logger.info(f"[WEATHER] Getting weather for: {city}")
        
        async with httpx.AsyncClient() as client:
            # First, geocode the city
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            geo_response = await client.get(geocode_url, timeout=10)
            geo_data = geo_response.json()
            
            if "results" not in geo_data or len(geo_data["results"]) == 0:
                return f"Could not find city: {city}"
            
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            city_name = location.get("name", city)
            country = location.get("country", "")
            
            # Get weather
            temp_unit = "fahrenheit" if unit.lower() == "fahrenheit" else "celsius"
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                f"&temperature_unit={temp_unit}"
            )
            
            weather_response = await client.get(weather_url, timeout=10)
            weather_data = weather_response.json()
            
            current = weather_data.get("current", {})
            temp = current.get("temperature_2m", "N/A")
            humidity = current.get("relative_humidity_2m", "N/A")
            wind = current.get("wind_speed_10m", "N/A")
            code = current.get("weather_code", 0)
            
            # Weather code descriptions
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Heavy showers",
                95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm",
            }
            
            condition = weather_codes.get(code, "Unknown")
            unit_symbol = "F" if temp_unit == "fahrenheit" else "C"
            
            return (
                f"Weather for {city_name}, {country}:\n"
                f"- Temperature: {temp} {unit_symbol}\n"
                f"- Condition: {condition}\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind} km/h"
            )
            
    except Exception as e:
        logger.error(f"[WEATHER] Failed: {str(e)}")
        return f"Error getting weather: {str(e)}"


# =============================================================================
# Run MCP Server
# =============================================================================
if __name__ == "__main__":
    mcp.run()
