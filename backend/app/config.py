"""
Configuration Management - Production-Grade
Uses Pydantic Settings for type-safe environment variable loading
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # =============================================================================
    # LLM Configuration (Groq)
    # =============================================================================
    groq_api_key: str = Field(..., description="Groq API key")
    groq_model: str = Field(default="llama-3.1-70b-versatile", description="Groq model name")
    groq_temperature: float = Field(default=0.0, description="LLM temperature")
    
    # =============================================================================
    # Embeddings (HuggingFace Inference API)
    # =============================================================================
    huggingface_api_key: str = Field(..., description="HuggingFace API token")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    
    # =============================================================================
    # Reranker (Jina AI)
    # =============================================================================
    jina_api_key: str = Field(..., description="Jina AI API key")
    jina_model: str = Field(
        default="jina-reranker-v2-base-multilingual",
        description="Jina reranker model"
    )
    
    # =============================================================================
    # Web Search (Tavily)
    # =============================================================================
    tavily_api_key: str = Field(..., description="Tavily API key for web search")
    
    # =============================================================================
    # Weather (Open-Meteo)
    # =============================================================================
    open_meteo_url: str = Field(
        default="https://api.open-meteo.com/v1/forecast",
        description="Open-Meteo API URL (no key required)"
    )
    
    # =============================================================================
    # RAG Pipeline Configuration
    # =============================================================================
    chunk_size: int = Field(default=1000, description="Text chunk size")
    chunk_overlap: int = Field(default=200, description="Text chunk overlap")
    vector_top_k: int = Field(default=20, description="Top K for vector search")
    bm25_top_k: int = Field(default=20, description="Top K for BM25 search")
    rrf_k: int = Field(default=60, description="RRF constant")
    final_top_k: int = Field(default=3, description="Final top K after reranking")
    
    # =============================================================================
    # MCP Server URLs
    # =============================================================================
    mcp_rag_url: str = Field(default="http://localhost:8001", description="RAG MCP server URL")
    mcp_sql_url: str = Field(default="http://localhost:8002", description="SQL MCP server URL")
    mcp_web_url: str = Field(default="http://localhost:8003", description="Web MCP server URL")
    mcp_weather_url: str = Field(default="http://localhost:8004", description="Weather MCP server URL")
    
    # =============================================================================
    # Database Configuration
    # =============================================================================
    database_url: str = Field(
        default="sqlite:///./rbac_chatbot.db",
        description="Database connection URL"
    )
    chromadb_path: str = Field(default="./chromadb", description="ChromaDB storage path")
    
    # =============================================================================
    # JWT Authentication
    # =============================================================================
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    
    # =============================================================================
    # Logging Configuration
    # =============================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_rag_chunks: bool = Field(default=True, description="Log RAG chunks with scores")
    log_llm_responses: bool = Field(default=True, description="Log all LLM responses")
    log_tool_calls: bool = Field(default=True, description="Log all tool executions")
    
    # =============================================================================
    # Rate Limiting
    # =============================================================================
    rate_limit_per_user: int = Field(
        default=30,
        description="Requests per minute per user"
    )
    
    # =============================================================================
    # Data Paths
    # =============================================================================
    data_dir: str = Field(
        default="C:/Users/Admin/RBAC_Agentic_Chatbot/data",
        description="Path to data directory"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# =============================================================================
# Global settings instance
# =============================================================================
settings = Settings()
