"""
Reciprocal Rank Fusion (RRF) - Hybrid Search Fusion
Adapted from user's src/retrieval/hybrid_fusion.py
"""

from typing import List, Dict, Any
from collections import defaultdict

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = None
) -> List[Dict[str, Any]]:
    """
    Combine vector and BM25 results using Reciprocal Rank Fusion
    
    Args:
        vector_results: Vector search results with 'vector_score'
        bm25_results: BM25 results with 'bm25_score'
        k: RRF constant (default from settings)
    
    Returns:
        Combined and sorted results with RRF scores
    """
    if k is None:
        k = settings.rrf_k
    
    rrf_scores = defaultdict(float)
    doc_data = {}
    
    # Add vector search scores
    for rank, doc in enumerate(vector_results, start=1):
        # Use text as ID for matching (since BM25 and vector may have different IDs)
        doc_id = doc.get('text', '')[:100]  # Use first 100 chars as identifier
        
        if not doc_id:
            continue
        
        rrf_scores[doc_id] += 1.0 / (k + rank)
        doc_data[doc_id] = doc.copy()
        doc_data[doc_id]['vector_score'] = doc.get('vector_score', 0.0)
    
    # Add BM25 scores
    for rank, doc in enumerate(bm25_results, start=1):
        doc_id = doc.get('text', '')[:100]
        
        if not doc_id:
            continue
        
        rrf_scores[doc_id] += 1.0 / (k + rank)
        
        if doc_id not in doc_data:
            doc_data[doc_id] = doc.copy()
            doc_data[doc_id]['vector_score'] = 0.0
        
        doc_data[doc_id]['bm25_score'] = doc.get('bm25_score', 0.0)
    
    # Sort by RRF score
    sorted_results = []
    for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
        doc = doc_data[doc_id]
        doc['rrf_score'] = rrf_score
        sorted_results.append(doc)
    
    logger.debug(f"RRF fusion: {len(sorted_results)} unique documents")
    return sorted_results
