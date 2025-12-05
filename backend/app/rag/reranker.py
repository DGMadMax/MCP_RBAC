"""
Jina AI Reranker - Cloud-based Cross-Encoder Reranking
"""

import httpx
from typing import List, Dict, Any

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class JinaReranker:
    """
    Jina AI reranker for precision improvement
    Uses cloud API (not local model)
    """
    
    def __init__(self):
        """Initialize Jina reranker"""
        self.api_key = settings.jina_api_key
        self.model = settings.jina_model
        self.api_url = "https://api.jina.ai/v1/rerank"
        
        logger.info(f"[OK] Jina reranker initialized (model: {self.model})")
    
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using Jina AI API
        
        Args:
            query: Search query
            documents: List of candidate documents
            top_k: Number of top results to return
        
        Returns:
            Top-k reranked documents with scores
        """
        if not documents:
            return []
        
        logger.debug(f"Reranking {len(documents)} documents with Jina AI...")
        
        try:
            # Prepare documents for reranking
            doc_texts = [doc.get('text', '') for doc in documents]
            
            # Call Jina API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": doc_texts,
                        "top_n": top_k
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
            
            # Extract reranked results
            reranked_docs = []
            for item in result.get("results", []):
                idx = item["index"]
                score = item["relevance_score"]
                
                doc = documents[idx].copy()
                doc['rerank_score'] = float(score)
                reranked_docs.append(doc)
            
            logger.debug(
                f"Reranked {len(documents)} → {len(reranked_docs)} documents | "
                f"Top score: {reranked_docs[0]['rerank_score']:.4f}" if reranked_docs else "No results"
            )
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Jina reranking failed: {str(e)}")
            # Fallback: return top k documents by RRF score
            logger.warning("Falling back to RRF scores...")
            sorted_docs = sorted(
                documents,
                key=lambda x: x.get('rrf_score', 0),
                reverse=True
            )
            return sorted_docs[:top_k]
