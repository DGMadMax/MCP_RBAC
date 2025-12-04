"""
Web Search MCP Server - Tavily API (via LangChain)
Port: 8003
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import time

from langchain_community.tools.tavily_search import TavilySearchResults

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(
    title="Web Search MCP Server",
    description="Web search using Tavily API with LangChain integration",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Initialize Tavily Search Tool
# =============================================================================
# LangChain TavilySearchResults uses TAVILY_API_KEY from environment
tavily_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",  # "basic" or "advanced"
    include_answer=True,
    include_raw_content=False,
    include_images=False,
)


# =============================================================================
# Schemas
# =============================================================================
class WebSearchRequest(BaseModel):
    query: str
    user_id: int
    max_results: int = 5


class WebSearchResponse(BaseModel):
    success: bool
    answer: str = ""
    sources: List[str] = []
    query_time_ms: float = 0.0
    model_used: str = "tavily-advanced"
    error: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================
@app.post("/search", response_model=WebSearchResponse)
async def web_search(request: WebSearchRequest):
    """
    Web search using Tavily API via LangChain
    
    Features:
    - Real-time web search
    - High-quality sources
    - AI-generated answer summary
    """
    try:
        logger.info(f"Web search request from user {request.user_id}: {request.query[:100]}...")
        
        start_time = time.time()
        
        # Invoke Tavily search (sync tool, but fast)
        results = tavily_search.invoke(request.query)
        
        query_time = (time.time() - start_time) * 1000
        
        # Parse results
        sources = []
        content_parts = []
        
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    url = result.get("url", "")
                    content = result.get("content", "")
                    
                    if url:
                        sources.append(url)
                    if content:
                        content_parts.append(content)
        
        # Combine content into answer
        answer = "\n\n".join(content_parts) if content_parts else "No results found."
        
        logger.info(f"Web search successful | Time: {query_time:.2f}ms | Sources: {len(sources)}")
        
        return WebSearchResponse(
            success=True,
            answer=answer,
            sources=sources,
            query_time_ms=round(query_time, 2),
            model_used="tavily-advanced"
        )
        
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        return WebSearchResponse(
            success=False,
            error=str(e)
        )


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Web Search MCP Server",
        "port": 8003,
        "api_configured": bool(settings.tavily_api_key)
    }


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
