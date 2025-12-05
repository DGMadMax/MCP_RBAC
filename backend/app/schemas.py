"""
Pydantic Schemas - Request/Response Models
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# =============================================================================
# Authentication Schemas
# =============================================================================
class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: str  # "Engineering Team", "Finance Team", etc.
    department: str  # "engineering", "finance", etc.


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response data"""
    id: int
    email: str
    full_name: str
    role: str
    department: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# Chat Schemas
# =============================================================================
class ChatRequest(BaseModel):
    """Chat request"""
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    query: str
    response: str
    tools_used: List[str]
    sources: List[Dict[str, str]]
    intent: str
    confidence: Optional[str] = None
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history item"""
    id: int
    query: str
    response: str
    tools_used: Optional[List[str]]
    sources: Optional[List[Dict[str, str]]]
    intent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    """Feedback request"""
    query: str
    answer: str
    rating: int
    helpful: bool
    comment: Optional[str] = None
    sources_count: Optional[int] = 0
    confidence: Optional[float] = None


# =============================================================================
# MCP Request/Response Schemas
# =============================================================================
class RAGSearchRequest(BaseModel):
    """RAG search request to MCP server"""
    query: str
    user_department: str
    user_role: str
    user_id: int
    top_k: int = 3


class RAGSearchResponse(BaseModel):
    """RAG search response from MCP server"""
    success: bool
    results: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SQLQueryRequest(BaseModel):
    """SQL query request to MCP server"""
    query: str
    user_role: str
    user_id: int


class SQLQueryResponse(BaseModel):
    """SQL query response from MCP server"""
    success: bool
    sql: Optional[str] = None
    result: Optional[str] = None
    row_count: Optional[int] = None
    error: Optional[str] = None


class WebSearchRequest(BaseModel):
    """Web search request to MCP server"""
    query: str
    user_id: int
    recency_filter: str = "month"


class WebSearchResponse(BaseModel):
    """Web search response from MCP server"""
    success: bool
    answer: str
    sources: List[str] = []
    query_time_ms: float
    model_used: str = "tavily-advanced"
    error: Optional[str] = None


class WeatherRequest(BaseModel):
    """Weather request to MCP server"""
    query: str
    user_id: int


class WeatherResponse(BaseModel):
    """Weather response from MCP server"""
    success: bool
    city: Optional[str] = None
    temperature: Optional[float] = None
    windspeed: Optional[float] = None
    formatted: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Health Check Schemas
# =============================================================================
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    mcp_server: Dict[str, Any]  # Updated for new MCP architecture


class MCPServerHealth(BaseModel):
    """MCP server health status"""
    rag_server: str
    sql_server: str
    web_server: str
    weather_server: str
