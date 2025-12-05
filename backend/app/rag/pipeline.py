"""
Complete RAG Pipeline - Hybrid Search → RRF → Reranking → RBAC Filtering
"""

import time
from typing import List, Dict, Any, Optional

from app.rag.vector_search import VectorSearchEngine
from app.rag.bm25_search import BM25SearchEngine
from app.rag.fusion import reciprocal_rank_fusion
from app.rag.reranker import JinaReranker
from app.config import settings
from app.logger import get_logger, log_chunks

logger = get_logger(__name__)


class RAGPipeline:
    """
    Complete RAG retrieval pipeline:
    1. Vector search (semantic) → Top 20
    2. BM25 search (keyword) → Top 20
    3. RRF fusion → Top 20 merged
    4. Jina reranking → Top 3
    5. RBAC filtering → Final results
    """
    
    def __init__(self):
        """Initialize RAG pipeline"""
        logger.info("Initializing RAG pipeline...")
        
        self.vector_engine = VectorSearchEngine()
        self.bm25_engine = BM25SearchEngine()
        self.reranker = JinaReranker()
        
        logger.info("[OK] RAG pipeline ready")
    
    async def retrieve(
        self,
        query: str,
        user_department: str,
        user_role: str,
        top_k_final: int = None
    ) -> Dict[str, Any]:
        """
        Complete retrieval pipeline with RBAC filtering
        
        Args:
            query: User query
            user_department: User's department for RBAC
            user_role: User's role (e.g., "C-Level", "Engineering Team")
            top_k_final: Number of final results (default from settings)
        
        Returns:
            Dictionary with results and metadata
        """
        if top_k_final is None:
            top_k_final = settings.final_top_k
        
        start_time = time.time()
        
        logger.info(f"RAG pipeline query: {query[:100]}... | User: {user_department}/{user_role}")
        
        # =====================================================================
        # Stage 1: Vector Search (Semantic)
        # =====================================================================
        logger.debug("[STAGE 1] Vector search...")
        vector_start = time.time()
        
        # RBAC filter for vector search
        if user_role == "C-Level":
            filter_dict = None  # C-Level sees everything
        else:
            filter_dict = {
                "department": {"$in": [user_department, "general"]}
            }
        
        vector_results = await self.vector_engine.search(
            query=query,
            top_k=settings.vector_top_k,
            filter_dict=filter_dict
        )
        
        vector_time = (time.time() - vector_start) * 1000
        if settings.log_rag_chunks:
            log_chunks(logger, vector_results, "VECTOR")
        
        # =====================================================================
        # Stage 2: BM25 Search (Keyword)
        # =====================================================================
        logger.debug("[STAGE 2] BM25 search...")
        bm25_start = time.time()
        
        bm25_results = await self.bm25_engine.search(
            query=query,
            top_k=settings.bm25_top_k
        )
        
        # Apply RBAC post-filter to BM25 results
        if user_role != "C-Level":
            bm25_results = [
                r for r in bm25_results
                if r.get('metadata', {}).get('department') in [user_department, "general"]
            ]
        
        bm25_time = (time.time() - bm25_start) * 1000
        if settings.log_rag_chunks:
            log_chunks(logger, bm25_results, "BM25")
        
        # =====================================================================
        # Stage 3: RRF Fusion
        # =====================================================================
        logger.debug("[STAGE 3] RRF fusion...")
        rrf_start = time.time()
        
        fused_results = reciprocal_rank_fusion(vector_results, bm25_results)
        fused_results = fused_results[:settings.vector_top_k]  # Top 20 after fusion
        
        rrf_time = (time.time() - rrf_start) * 1000
        if settings.log_rag_chunks:
            log_chunks(logger, fused_results, "RRF")
        
        # =====================================================================
        # Stage 4: Jina Reranking
        # =====================================================================
        logger.debug("[STAGE 4] Jina reranking...")
        rerank_start = time.time()
        
        reranked_results = await self.reranker.rerank(
            query=query,
            documents=fused_results,
            top_k=top_k_final
        )
        
        rerank_time = (time.time() - rerank_start) * 1000
        if settings.log_rag_chunks:
            log_chunks(logger, reranked_results, "RERANKED")
        
        # =====================================================================
        # Stage 5: Final RBAC Check (paranoid mode)
        # =====================================================================
        if user_role != "C-Level":
            reranked_results = [
                r for r in reranked_results
                if r.get('metadata', {}).get('department') in [user_department, "general"]
            ]
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"[OK] RAG pipeline complete | "
            f"Total: {total_time:.2f}ms | "
            f"Vector: {vector_time:.2f}ms | "
            f"BM25: {bm25_time:.2f}ms | "
            f"RRF: {rrf_time:.2f}ms | "
            f"Rerank: {rerank_time:.2f}ms | "
            f"Results: {len(reranked_results)}"
        )
        
        return {
            "success": True,
            "results": reranked_results,
            "metadata": {
                "query": query,
                "user_department": user_department,
                "user_role": user_role,
                "total_time_ms": round(total_time, 2),
                "vector_count": len(vector_results),
                "bm25_count": len(bm25_results),
                "fused_count": len(fused_results),
                "final_count": len(reranked_results),
                "stage_times_ms": {
                    "vector": round(vector_time, 2),
                    "bm25": round(bm25_time, 2),
                    "rrf": round(rrf_time, 2),
                    "rerank": round(rerank_time, 2)
                }
            }
        }
