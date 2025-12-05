# RBAC Agentic AI Chatbot - Test Suite

Production-grade unit tests for the MCP + LangGraph architecture.

## Test Files

| File | Coverage |
|------|----------|
| `test_mcp_server.py` | MCP tools (RAG, SQL, Web, Weather) |
| `test_agent_graph.py` | LangGraph agent (router, executor, generator) |
| `test_api_routes.py` | API routes, auth, rate limiting |
| `test_rag_pipeline.py` | RAG pipeline (vector, BM25, fusion) |
| `test_auth.py` | JWT authentication, password hashing |
| `conftest.py` | Pytest fixtures and configuration |

## Running Tests

```bash
# From backend directory
cd backend

# Run all tests
py -m pytest tests/ -v

# Run specific test file
py -m pytest tests/test_mcp_server.py -v

# Run with coverage
py -m pytest tests/ --cov=app --cov-report=html

# Run only async tests
py -m pytest tests/ -v -m asyncio
```

## Test Architecture

```
tests/
├── conftest.py           # Shared fixtures (test_db, test_user, mock data)
├── test_mcp_server.py    # MCP tool unit tests
├── test_agent_graph.py   # LangGraph workflow tests
├── test_api_routes.py    # FastAPI route tests
├── test_rag_pipeline.py  # RAG component tests
└── test_auth.py          # Authentication tests
```

## Key Fixtures

| Fixture | Description |
|---------|-------------|
| `test_db` | In-memory SQLite database |
| `test_user` | Engineering team user |
| `test_admin_user` | C-Level admin user |
| `auth_headers` | JWT auth headers for test_user |
| `admin_auth_headers` | JWT auth headers for admin |
| `mock_rag_results` | Mock RAG search results |
| `mock_sql_results` | Mock SQL query results |

## Test Categories

### 1. MCP Server Tests (`test_mcp_server.py`)
- `TestSearchDocuments` - RAG tool with RBAC filtering
- `TestQueryDatabase` - SQL tool with role restrictions
- `TestWebSearch` - Tavily web search integration
- `TestGetWeather` - Open-Meteo weather API
- `TestMCPServerInit` - Server initialization
- `TestSettingsIntegration` - Config settings

### 2. Agent Graph Tests (`test_agent_graph.py`)
- `TestRouterNode` - Intent classification
- `TestToolExecutorNode` - Tool execution
- `TestGeneratorNode` - Response synthesis
- `TestAgentGraph` - Graph compilation
- `TestConditionalRouting` - Edge conditions

### 3. API Route Tests (`test_api_routes.py`)
- `TestAuthRoutes` - Register, login
- `TestHealthRoutes` - Health checks
- `TestChatRoutes` - Chat endpoints
- `TestRateLimiting` - SlowAPI rate limits
- `TestRBACFiltering` - Role-based access

## Mocking Strategy

External services are mocked to ensure:
- Fast test execution
- No API costs during testing
- Consistent test results

```python
# Example: Mocking Groq LLM
@pytest.fixture
def mock_groq_llm():
    with patch('app.agent.graph.ChatGroq') as mock:
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=MagicMock(content="response"))
        mock.return_value = llm
        yield llm
```

## CI/CD Integration

Tests are designed for CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    cd backend
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov
    pytest tests/ -v --cov=app
```

## Adding New Tests

1. Add fixtures to `conftest.py` if reusable
2. Create test class with descriptive name
3. Use `@pytest.mark.asyncio` for async tests
4. Mock external dependencies
5. Test both success and error cases
