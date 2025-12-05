"""
RAG Package - Hybrid Search Pipeline
"""

from app.rag.pipeline import RAGPipeline
from app.rag.vector_search import VectorSearchEngine
from app.rag.bm25_search import BM25SearchEngine
from app.rag.fusion import reciprocal_rank_fusion
from app.rag.reranker import JinaReranker
from app.logger import get_logger

logger = get_logger(__name__)

# Global RAG pipeline instance
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the RAG pipeline singleton."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def hybrid_rag_search(
    query: str,
    user_department: str,
    user_role: str,
    top_k: int = 3
) -> list:
    """
    Synchronous wrapper for hybrid RAG search.
    Used by MCP tools.
    
    Args:
        query: Search query
        user_department: User's department for RBAC
        user_role: User's role
        top_k: Number of results
    
    Returns:
        List of document chunks with scores
    """
    import asyncio
    
    try:
        pipeline = get_rag_pipeline()
        
        # Run async method in sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, use run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(
                pipeline.retrieve(
                    query=query,
                    user_department=user_department,
                    user_role=user_role,
                    top_k_final=top_k
                ),
                loop
            )
            result = future.result(timeout=30)
        else:
            result = asyncio.run(
                pipeline.retrieve(
                    query=query,
                    user_department=user_department,
                    user_role=user_role,
                    top_k_final=top_k
                )
            )
        
        if result.get("success") and result.get("results"):
            # Format results for MCP tool
            formatted = []
            for chunk in result["results"]:
                formatted.append({
                    "content": chunk.get("content", ""),
                    "source": chunk.get("metadata", {}).get("source", "Unknown"),
                    "score": chunk.get("score", 0)
                })
            return formatted
        
        return []
        
    except Exception as e:
        logger.error(f"[RAG] hybrid_rag_search error: {str(e)}")
        return []


__all__ = [
    "RAGPipeline",
    "VectorSearchEngine",
    "BM25SearchEngine",
    "reciprocal_rank_fusion",
    "JinaReranker",
    "get_rag_pipeline",
    "hybrid_rag_search",
]
