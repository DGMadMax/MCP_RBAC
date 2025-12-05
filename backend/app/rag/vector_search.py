"""
Vector Search Engine - ChromaDB with HuggingFace Inference API
"""

from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class VectorSearchEngine:
    """
    Vector search using ChromaDB and HuggingFace Inference API embeddings
    """
    
    def __init__(self):
        """Initialize vector search engine"""
        logger.info("Initializing vector search engine...")
        
        # HuggingFace Inference API embeddings (NOT local!)
        self.embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=settings.huggingface_api_key,
            model_name=settings.embedding_model
        )
        
        # ChromaDB vector store
        self.vectorstore = Chroma(
            collection_name="rbac_documents",
            embedding_function=self.embeddings,
            persist_directory=settings.chromadb_path
        )
        
        logger.info("[OK] Vector search engine initialized")
    
    async def search(
        self,
        query: str,
        top_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Metadata filter (e.g., {"department": {"$in": ["engineering", "general"]}})
        
        Returns:
            List of search results with scores and metadata
        """
        logger.debug(f"Vector search query: {query[:100]}... | top_k={top_k}")
        
        try:
            # Perform similarity search with scores
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=top_k,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "id": doc.metadata.get("chunk_id", 0),
                    "text": doc.page_content,
                    "vector_score": float(score),
                    "metadata": doc.metadata
                })
            
            logger.debug(f"Vector search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
