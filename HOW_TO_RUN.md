# How to Run RBAC Agentic AI Chatbot

**Complete guide to run the backend and frontend applications**

---

## Prerequisites

### Required Software
- **Python 3.11+** (Python 3.13 recommended)
- **Node.js 18+** and **npm**
- **Git** (for cloning)

### Check Installation
```powershell
# Check Python
py --version  # Should show Python 3.11 or higher

# Check Node.js
node --version  # Should show v18 or higher
npm --version
```

---

## Project Structure

```
RBAC_Agentic_Chatbot/
├── backend/                 # FastAPI + MCP + LangGraph
│   ├── .venv/              # Virtual environment
│   ├── app/                # Application code
│   ├── tests/              # Unit tests
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Environment variables
└── frontend/               # React + TypeScript
    ├── src/                # Source code
    ├── package.json        # Node dependencies
    └── .env                # Frontend config
```

---

## Backend Setup & Run

### Step 1: Navigate to Backend
```powershell
cd C:\Users\Admin\RBAC_Agentic_Chatbot\backend
```

### Step 2: Configure Environment Variables
```powershell
# Copy example file
Copy-Item .env.example .env

# Edit .env and add your API keys
notepad .env
```

**Required API Keys:**
```env
# Python Configuration
PYTHONDONTWRITEBYTECODE=1  # Prevent __pycache__ folders

# API Keys
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_token_here
JINA_API_KEY=your_jina_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
JWT_SECRET_KEY=your_super_secret_jwt_key_here
```

### Step 3: Activate Virtual Environment & Install Dependencies

> **Note:** The virtual environment is already created at `.venv`

```powershell
# Activate venv (if not already active)
.\.venv\Scripts\Activate.ps1

# If activation fails due to execution policy, use python directly:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 4: Initialize Database (Optional - runs automatically)
```powershell
# Seed sample data (optional)
.\.venv\Scripts\python.exe seed_database.py

# Ingest RAG documents (optional)
.\.venv\Scripts\python.exe ingest_data.py
```

### Step 5: Run Backend Server

**Using Virtual Environment (RECOMMENDED):**
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**With Hot Reload (Development):**
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Backend Endpoints

Once running, access:

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/` | API root |
| `http://localhost:8000/docs` | Interactive API docs (Swagger) |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/mcp` | MCP server endpoint |

---

## Frontend Setup & Run

### Step 1: Navigate to Frontend
```powershell
# Open a NEW terminal (keep backend running)
cd C:\Users\Admin\RBAC_Agentic_Chatbot\frontend
```

### Step 2: Install Dependencies
```powershell
# First time only
npm install
```

### Step 3: Configure Environment
```powershell
# Create .env file (if not exists)
echo "VITE_API_URL=http://localhost:8000" > .env
```

### Step 4: Run Frontend Development Server
```powershell
npm run dev
```

### Frontend Access

Open browser:
```
http://localhost:5173
```

---

## Running Both (Quick Start)

### Terminal 1 - Backend
```powershell
cd C:\Users\Admin\RBAC_Agentic_Chatbot\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Wait for: `✅ Application ready!`

### Terminal 2 - Frontend
```powershell
cd C:\Users\Admin\RBAC_Agentic_Chatbot\frontend
npm run dev
```

Wait for: `Local: http://localhost:5173/`

### Access Application
```
http://localhost:5173
```

---

## Testing the Application

### 1. Test Backend Health
```powershell
# In a new terminal
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-05T...",
  "database": "connected",
  "mcp_server": {
    "status": "healthy",
    "endpoint": "/mcp",
    "transport": "Streamable HTTP",
    "tools": ["search_documents", "query_database", "web_search", "get_weather"]
  }
}
```

### 2. Run Backend Unit Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### 3. Run Tests with Coverage
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --cov=app --cov-report=html
```

---

## Default Credentials

After seeding the database, use these credentials:

| Role | Email | Password |
|------|-------|----------|
| C-Level | clevel@company.com | admin123 |
| Engineering | eng@company.com | eng123 |
| Finance | finance@company.com | fin123 |
| HR | hr@company.com | hr123 |
| Marketing | marketing@company.com | mkt123 |

---

## Architecture Overview

### MCP (Model Context Protocol) Implementation

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                                                             │
│  ┌─────────────┐        JSON-RPC 2.0       ┌─────────────┐  │
│  │ MCP CLIENT  │◄─────────────────────────►│ MCP SERVER  │  │
│  │ClientSession│   Streamable HTTP /mcp    │  FastMCP    │  │
│  └─────────────┘                           └─────────────┘  │
│        ▲                                         │          │
│        │                                         │          │
│  ┌─────┴─────┐                            ┌─────▼─────┐    │
│  │ LangGraph │                            │ 4 Tools:  │    │
│  │  Agent    │                            │ - RAG     │    │
│  └───────────┘                            │ - SQL     │    │
│                                           │ - Web     │    │
│                                           │ - Weather │    │
│                                           └───────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI + Uvicorn
- Official MCP SDK (Streamable HTTP)
- LangGraph (Agent orchestration)
- Groq (LLM)
- ChromaDB (Vector store)
- SQLite (Relational DB)

**Frontend:**
- React 18 + TypeScript
- Vite
- TailwindCSS
- Lucide Icons

---

## Troubleshooting

### Port Already in Use

**Error:** `[Errno 10048] error while attempting to bind on address`

**Solution:**
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Kill the process (replace PID)
Stop-Process -Id <PID>

# Or use a different port
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

### Virtual Environment Not Activating

**Error:** `running scripts is disabled on this system`

**Solution:**
```powershell
# Option 1: Use python directly without activation
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# Option 2: Change execution policy (admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
```powershell
# Reinstall dependencies in venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Database Locked

**Error:** `database is locked`

**Solution:**
```powershell
# Delete database file and restart
Remove-Item rbac_chatbot.db
.\.venv\Scripts\python.exe seed_database.py
```

### Frontend Can't Connect to Backend

**Error:** `Network Error` or `Failed to fetch`

**Solution:**
1. Verify backend is running: `http://localhost:8000/health`
2. Check CORS settings in `backend/app/main.py`
3. Verify `VITE_API_URL` in `frontend/.env`

---

## Stopping the Applications

### Stop Backend
```
Press CTRL+C in the backend terminal
```

### Stop Frontend
```
Press CTRL+C in the frontend terminal
```

---

## Production Deployment

### Backend
```powershell
# Install production dependencies
.\.venv\Scripts\python.exe -m pip install gunicorn

# Run with Gunicorn (Linux) or Uvicorn workers (Windows)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend
```powershell
# Build for production
npm run build

# Serve built files (use nginx or serve)
npm install -g serve
serve -s dist -p 3000
```

---

## Additional Commands

### Backend Commands
```powershell
# Run specific tests
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_server.py -v

# Check code style
.\.venv\Scripts\python.exe -m flake8 app/

# Format code
.\.venv\Scripts\python.exe -m black app/
```

### Frontend Commands
```powershell
# Lint
npm run lint

# Build
npm run build

# Preview production build
npm run preview
```

---

## Getting Help

- **Backend Logs:** `backend/logs/application_YYYYMMDD.log`
- **API Documentation:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`
- **MCP Inspector:** Use official MCP inspector to test MCP server

---

## Architecture Documentation

For detailed architecture information, see:
- [Implementation Plan](C:\Users\Admin\.gemini\antigravity\brain\d88613f3-c6c0-4715-b20c-ef70fc30d17b\implementation_plan.md)
- [Debug Report](C:\Users\Admin\.gemini\antigravity\brain\d88613f3-c6c0-4715-b20c-ef70fc30d17b\debug_report.md)
- [Test Documentation](backend/tests/README.md)

---

**Last Updated:** 2025-12-05
