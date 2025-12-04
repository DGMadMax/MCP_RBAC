"""
RAG MCP Server - Hybrid Search with RBAC
Port: 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from app.rag.pipeline import RAGPipeline
from app.logger import get_logger, log_chunks
from app.config import settings

logger = get_logger(__name__)

# =============================================================================
# FastAPI App
# =============================================================================
app = FastAPI(
    title="RAG MCP Server",
    description="Hybrid search with vector + BM25 + RRF + Jina reranking",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag_pipeline: Optional[RAGPipeline] = None


# =============================================================================
# Schemas
# =============================================================================
class SearchRequest(BaseModel):
    query: str
    user_department: str
    user_role: str
    user_id: int
    top_k: int = 3


class SearchResponse(BaseModel):
    success: bool
    results: list
    metadata: Optional[dict] = None
    error: Optional[str] = None


# =============================================================================
# Startup/Shutdown
# =============================================================================
@app.on_event("startup")
async def startup():
    """Initialize RAG pipeline on startup"""
    global rag_pipeline
    logger.info("=" * 80)
    logger.info("🔍 Starting RAG MCP Server on port 8001...")
    logger.info("=" * 80)
    
    try:
        rag_pipeline = RAGPipeline()
        logger.info("✅ RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG pipeline: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down RAG MCP Server...")


# =============================================================================
# Endpoints
# =============================================================================
@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Hybrid search with RBAC filtering
    
    Pipeline:
    1. Vector search (ChromaDB) → Top 20
    2. BM25 search → Top 20
    3. RRF fusion → Top 20 merged
    4. Jina reranker → Top K
    5. RBAC filter by department
    """
    try:
        logger.info(f"RAG search request from user {request.user_id} ({request.user_role}/{request.user_department})")
        
        # Execute RAG pipeline
        result = await rag_pipeline.retrieve(
            query=request.query,
            user_department=request.user_department,
            user_role=request.user_role,
            top_k_final=request.top_k
        )
        
        return SearchResponse(**result)
        
    except Exception as e:
        logger.error(f"RAG search failed: {str(e)}")
        return SearchResponse(
            success=False,
            results=[],
            error=str(e)
        )


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "RAG MCP Server",
        "port": 8001,
        "pipeline_ready": rag_pipeline is not None
    }


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
