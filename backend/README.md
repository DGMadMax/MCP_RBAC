# RBAC Agentic AI Chatbot - Backend README

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required:
# - GROQ_API_KEY
# - HUGGINGFACE_API_KEY  
# - JINA_API_KEY
# - PERPLEXITY_API_KEY
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database & Data
```bash
# Create demo users (6 roles)
python seed_database.py

# Ingest documents and HR data (one-time)
python ingest_data.py
```

### 4. Start MCP Servers
```bash
# In a separate terminal
python -m app.mcp_servers
```

This starts all 4 MCP servers:
- RAG Server: http://localhost:8001
- SQL Server: http://localhost:8002
- Web Server: http://localhost:8003
- Weather Server: http://localhost:8004

### 5. Start Main Application
```bash
# In another terminal
python -m app.main

# Or with uvicorn:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Main API: http://localhost:8000

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Pydantic settings
│   ├── logger.py               # Centralized logging
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   │
│   ├── auth/                   # Authentication
│   │   ├── jwt.py
│   │   ├── password.py
│   │   └── dependencies.py
│   │
│   ├── rag/                    # RAG Pipeline
│   │   ├── vector_search.py
│   │   ├── bm25_search.py
│   │   ├── fusion.py           # RRF
│   │   ├── reranker.py         # Jina API
│   │   └── pipeline.py
│   │
│   ├── mcp_servers/            # 4 MCP Servers
│   │   ├── __main__.py         # Multi-process orchestrator
│   │   ├── rag_server.py
│   │   ├── sql_server.py
│   │   ├── web_server.py
│   │   └── weather_server.py
│   │
│   ├── mcp_client/             # MCP Client Wrappers
│   │   └── client.py
│   │
│   ├── agent/                  # LangGraph Workflow
│   │   ├── state.py
│   │   ├── prompts.py
│   │   ├── nodes.py
│   │   └── graph.py
│   │
│   └── routes/                 # FastAPI Routes
│       ├── auth.py
│       ├── chat.py
│       └── health.py
│
├── seed_database.py            # Demo user creation
├── ingest_data.py              # One-time data ingestion
├── requirements.txt
└── .env.example
```

---

## 🔑 Demo User Credentials

| Email | Password | Role | Department | Access |
|-------|----------|------|------------|--------|
| admin@test.com | admin123 | C-Level | c-level | ALL departments |
| engineering@test.com | eng123 | Engineering Team | engineering | engineering + general |
| finance@test.com | fin123 | Finance Team | finance | finance + general |
| hr@test.com | hr123 | HR Team | hr | hr + general |
| marketing@test.com | mkt123 | Marketing Team | marketing | marketing + general |
| employee@test.com | emp123 | Employee | general | general only |

---

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (returns JWT token)

### Chat
- `POST /chat` - Synchronous chat
- `POST /chat/stream` - SSE streaming chat
- `GET /chat/history` - Get chat history

### Monitoring
- `GET /health` - System health check
- `GET /mcp/health` - MCP server statuses

---

## 🧪 Testing the System

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "engineering@test.com", "password": "eng123"}'
```

### 3. Chat (with token)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"query": "What is FinSolve'\''s system architecture?"}'
```

---

## 🔍 Logs

Logs are stored in `logs/` directory:
- `application_YYYYMMDD.log` - All application logs
- `debug_YYYYMMDD.log` - Debug logs (RAG pipeline details)

---

## ⚙️ Configuration

All settings are in `.env` file. Key configurations:

**API Keys**: Groq, HuggingFace, Jina, Perplexity  
**RRF Settings**: `RRF_K=60`  
**Top K**: Vector=20, BM25=20, Final=3  
**Chunk Size**: 1000 chars, Overlap=200  
**JWT Expiry**: 30 minutes

---

## 🛠️ Development

### Run with auto-reload:
```bash
uvicorn app.main:app --reload
```

### View API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 Troubleshooting

**MCP Servers not responding?**
- Check if servers are running: `python -m app.mcp_servers`
- Verify ports 8001-8004 are available

**ChromaDB errors?**
- Delete `chromadb/` folder
- Re-run: `python ingest_data.py`

**Authentication errors?**
- Check JWT_SECRET_KEY in `.env`
- Verify user exists: check `rbac_chatbot.db`

---

## 📝 Notes

- Data ingestion is a ONE-TIME operation (idempotent)
- MCP servers must be running before starting main app
- All API calls require JWT authentication (except /auth endpoints)
- SSE streaming is recommended for better UX
