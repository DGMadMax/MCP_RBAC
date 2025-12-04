"""
Unit Tests for RAG Pipeline
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.rag.fusion import reciprocal_rank_fusion


class TestRRFFusion:
    """Test Reciprocal Rank Fusion algorithm"""
    
    def test_rrf_fusion_basic(self):
        """Test RRF with basic inputs"""
        vector_results = [
            {"text": "Document A", "vector_score": 0.95},
            {"text": "Document B", "vector_score": 0.85}
        ]
        
        bm25_results = [
            {"text": "Document B", "bm25_score": 0.90},
            {"text": "Document C", "bm25_score": 0.80}
        ]
        
        fused = reciprocal_rank_fusion(vector_results, bm25_results, k=60)
        
        assert len(fused) == 3
        assert "rrf_score" in fused[0]
        
        # Document B should rank high (appears in both)
        doc_b = [d for d in fused if "Document B" in d["text"]][0]
        assert doc_b["rrf_score"] > 0
    
    def test_rrf_fusion_empty_inputs(self):
        """Test RRF with empty inputs"""
        fused = reciprocal_rank_fusion([], [], k=60)
        assert len(fused) == 0
    
    def test_rrf_preserves_scores(self):
        """Test that RRF preserves original scores"""
        vector_results = [{"text": "Doc A", "vector_score": 0.9}]
        bm25_results = [{"text": "Doc A", "bm25_score": 0.8}]
        
        fused = reciprocal_rank_fusion(vector_results, bm25_results)
        
        assert fused[0]["vector_score"] == 0.9
        assert fused[0]["bm25_score"] == 0.8


class TestVectorSearch:
    """Test Vector Search Engine"""
    
    @patch("app.rag.vector_search.Chroma")
    @patch("app.rag.vector_search.HuggingFaceInferenceAPIEmbeddings")
    async def test_vector_search_initialization(self, mock_embeddings, mock_chroma):
        """Test vector search engine initialization"""
        from app.rag.vector_search import VectorSearchEngine
        
        engine = VectorSearchEngine()
        
        assert mock_embeddings.called
        assert mock_chroma.called
    
    @patch("app.rag.vector_search.Chroma")
    @patch("app.rag.vector_search.HuggingFaceInferenceAPIEmbeddings")
    async def test_vector_search_query(self, mock_embeddings, mock_chroma):
        """Test vector search query execution"""
        from app.rag.vector_search import VectorSearchEngine
        
        # Mock the search results
        mock_chroma.return_value.similarity_search_with_relevance_scores = AsyncMock(
            return_value=[
                (Mock(page_content="Test doc", metadata={"department": "engineering"}), 0.95)
            ]
        )
        
        engine = VectorSearchEngine()
        results = await engine.search("test query", top_k=5)
        
        # Should handle the mock gracefully
        assert isinstance(results, list)


class TestBM25Search:
    """Test BM25 Keyword Search"""
    
    @patch("app.rag.bm25_search.Chroma")
    @patch("app.rag.bm25_search.HuggingFaceInferenceAPIEmbeddings")
    async def test_bm25_initialization(self, mock_embeddings, mock_chroma):
        """Test BM25 initialization"""
        from app.rag.bm25_search import BM25SearchEngine
        
        # Mock document retrieval
        mock_collection = Mock()
        mock_collection.get.return_value = {
            "documents": ["doc1", "doc2"],
            "metadatas": [{"dept": "eng"}, {"dept": "hr"}]
        }
        mock_chroma.return_value._collection = mock_collection
        
        engine = BM25SearchEngine()
        
        assert len(engine.documents) == 2
        assert engine.bm25 is not None


class TestJinaReranker:
    """Test Jina AI Reranker"""
    
    @pytest.mark.asyncio
    async def test_reranker_success(self, monkeypatch):
        """Test reranker with successful API call"""
        from app.rag.reranker import JinaReranker
        
        # Mock httpx response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 1, "relevance_score": 0.85}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        async def mock_post(*args, **kwargs):
            return mock_response
        
        # Patch httpx.AsyncClient
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            reranker = JinaReranker()
            documents = [
                {"text": "Doc A", "rrf_score": 0.8},
                {"text": "Doc B", "rrf_score": 0.7}
            ]
            
            results = await reranker.rerank("query", documents, top_k=2)
            
            assert len(results) <= 2
            assert "rerank_score" in results[0]
    
    @pytest.mark.asyncio
    async def test_reranker_fallback(self):
        """Test reranker fallback on error"""
        from app.rag.reranker import JinaReranker
        
        # Force error by not mocking
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API Error")
            
            reranker = JinaReranker()
            documents = [
                {"text": "Doc A", "rrf_score": 0.8},
                {"text": "Doc B", "rrf_score": 0.7}
            ]
            
            # Should fall back to RRF scores
            results = await reranker.rerank("query", documents, top_k=1)
            
            assert len(results) == 1
            assert results[0]["text"] == "Doc A"  # Higher RRF score
