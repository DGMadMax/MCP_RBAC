# Test Suite - RBAC Agentic AI Chatbot

## 📦 Installation

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

## 🧪 Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run specific test class
```bash
pytest tests/test_auth.py::TestPasswordHashing
```

### Run specific test
```bash
pytest tests/test_auth.py::TestPasswordHashing::test_hash_password
```

### Run with verbose output
```bash
pytest -v
```

### Run only fast tests (skip slow ones)
```bash
pytest -m "not slow"
```

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Fixtures & configuration
├── test_auth.py             # Authentication tests
├── test_rag_pipeline.py     # RAG pipeline tests
├── test_agent_nodes.py      # LangGraph agent tests
├── test_api_routes.py       # FastAPI routes tests
└── test_mcp_client.py       # MCP client tests
```

## 🎯 Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Authentication | 8 | Password hashing, JWT tokens, User model |
| RAG Pipeline | 9 | RRF fusion, Vector search, BM25, Jina reranker |
| Agent Nodes | 8 | Orchestrator, Query rewriter, Tool executor, Synthesizer |
| API Routes | 10 | Auth routes, Chat routes, Health checks, RBAC |
| MCP Client | 8 | Base client, RAG/SQL/Web/Weather clients |

**Total**: ~43 unit tests

## 🏗️ Test Fixtures

### Database Fixtures
- `test_db` - In-memory SQLite database
- `test_user` - Engineering team user
- `test_admin_user` - C-Level admin user
- `test_employee` - Employee record

### Auth Fixtures
- `auth_headers` - JWT auth headers for regular user
- `admin_auth_headers` - JWT auth headers for admin

### Mock Data Fixtures
- `mock_rag_results` - Mock RAG search results
- `mock_sql_results` - Mock SQL query results
- `mock_web_results` - Mock web search results
- `mock_weather_results` - Mock weather data

## ✅ What's Tested

### ✓ Authentication
- Password hashing (bcrypt)
- Password verification
- JWT token creation
- JWT token verification
- User model CRUD

### ✓ RAG Pipeline
- RRF fusion algorithm
- Vector search initialization
- BM25 search initialization
- Jina reranker (success & fallback)

### ✓ Agent Nodes
- Intent classification (greeting, rag, sql, web, weather)
- Query rewriting (single & multi-part)
- Parallel tool execution
- Response synthesis

### ✓ API Routes
- User registration (success & duplicate email)
- User login (success & wrong password)
- Health checks
- Chat history with auth
- RBAC filtering

### ✓ MCP Client
- Successful API calls
- Timeout handling
- HTTP error handling
- All 4 specific clients (RAG, SQL, Web, Weather)

## 🔍 Mocking Strategy

Tests use `unittest.mock` to mock external dependencies:
- **LLM calls** (Groq) - Mocked to avoid API costs
- **Embeddings** (HuggingFace) - Mocked to avoid downloads
- **Reranker** (Jina) - Mocked to avoid API calls
- **Web search** (Perplexity) - Mocked
- **Weather API** (Open-Meteo) - Mocked
- **HTTP clients** - Mocked with httpx responses

## 📊 Example Test Output

```
tests/test_auth.py::TestPasswordHashing::test_hash_password PASSED         [ 12%]
tests/test_auth.py::TestPasswordHashing::test_verify_password_correct PASSED [ 25%]
tests/test_auth.py::TestJWT::test_create_access_token PASSED              [ 37%]
tests/test_rag_pipeline.py::TestRRFFusion::test_rrf_fusion_basic PASSED   [ 50%]
tests/test_agent_nodes.py::TestOrchestratorNode::test_orchestrator_greeting_intent PASSED [ 62%]
tests/test_api_routes.py::TestAuthRoutes::test_register_user_success PASSED [ 75%]
tests/test_mcp_client.py::TestRAGClient::test_rag_client_search PASSED    [ 87%]

======================== 43 passed in 2.34s ========================
```

## 🚀 Next Steps

To improve test coverage:
1. Add integration tests for full chat flow
2. Add load tests with Locust
3. Add E2E tests for MCP server communication
4. Add property-based tests with Hypothesis
5. Increase coverage to >80%
