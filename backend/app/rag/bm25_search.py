"""
BM25 Keyword Search Engine
"""

from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class BM25SearchEngine:
    """
    BM25 keyword search for lexical matching
    """
    
    def __init__(self):
        """Initialize BM25 search engine"""
        logger.info("Initializing BM25 search engine...")
        
        # Connect to ChromaDB to get documents
        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=settings.huggingface_api_key,
            model_name=settings.embedding_model
        )
        
        vectorstore = Chroma(
            collection_name="rbac_documents",
            embedding_function=embeddings,
            persist_directory=settings.chromadb_path
        )
        
        # Get all documents
        collection = vectorstore._collection
        all_docs = collection.get(include=["documents", "metadatas"])
        
        self.documents = all_docs["documents"]
        self.metadatas = all_docs["metadatas"]
        
        # Tokenize documents for BM25
        tokenized_corpus = [doc.lower().split() for doc in self.documents]
        
        # Build BM25 index
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        logger.info(f"[OK] BM25 index built with {len(self.documents)} documents")
    
    async def search(
        self,
        query: str,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of search results with BM25 scores
        """
        logger.debug(f"BM25 search query: {query[:100]}... | top_k={top_k}")
        
        try:
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores
            scores = self.bm25.get_scores(tokenized_query)
            
            # Get top k indices
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            
            # Format results
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include results with positive scores
                    results.append({
                        "id": idx,
                        "text": self.documents[idx],
                        "bm25_score": float(scores[idx]),
                        "metadata": self.metadatas[idx] if self.metadatas else {}
                    })
            
            logger.debug(f"BM25 search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {str(e)}")
            return []
