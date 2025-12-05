# MCP Inspector - Testing Your MCP Server

**Official tool from Anthropic to inspect and test MCP servers**

---

## What is MCP Inspector?

The MCP Inspector is a browser-based debugging tool that lets you:
- ✅ Connect to your MCP server
- ✅ View all available tools
- ✅ Test tool calls with custom arguments
- ✅ See JSON-RPC requests/responses
- ✅ Debug MCP protocol communication

---

## Installation

### Option 1: NPX (Recommended - No Installation)
```powershell
npx @modelcontextprotocol/inspector
```

### Option 2: Global Install
```powershell
npm install -g @modelcontextprotocol/inspector
mcp-inspector
```

---

## How to Use with Your MCP Server

### Step 1: Start Your Backend Server

Make sure your backend is running:
```powershell
cd C:\Users\Admin\RBAC_Agentic_Chatbot\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Wait for: `✅ Application ready!`

### Step 2: Launch MCP Inspector

In a **new terminal**:
```powershell
npx @modelcontextprotocol/inspector
```

This will open your browser automatically at `http://localhost:5173` (or similar)

### Step 3: Connect to Your MCP Server

In the MCP Inspector UI:

1. **Server URL:** Enter your MCP endpoint
   ```
   http://localhost:8000/mcp
   ```

2. **Transport:** Select **`HTTP`** or **`Streamable HTTP`**

3. **Click "Connect"**

---

## Testing Your Tools

Once connected, you'll see all 4 tools:

### 1. **search_documents** (RAG Tool)
```json
{
  "query": "What is the company policy on remote work?",
  "department": "engineering",
  "user_role": "Engineering Team",
  "top_k": 3
}
```

### 2. **query_database** (SQL Tool)
```json
{
  "query": "Show me all employees in engineering department",
  "user_role": "admin",
  "user_id": 1
}
```

### 3. **web_search** (Tavily Tool)
```json
{
  "query": "Latest news on AI agents",
  "max_results": 5
}
```

### 4. **get_weather** (Open-Meteo Tool)
```json
{
  "city": "Mumbai",
  "unit": "celsius"
}
```

---

## Inspector UI Sections

### 1. **Connection Panel** (Left)
- Server URL input
- Transport selection
- Connection status
- Tools list

### 2. **Tool Testing Panel** (Center)
- Selected tool name
- Arguments editor (JSON)
- Execute button
- Response viewer

### 3. **Protocol Viewer** (Right)
- Raw JSON-RPC requests
- Raw JSON-RPC responses
- Message IDs
- Error messages

---

## Example Workflow

### Test the RAG Tool:

1. **Select Tool:** Click `search_documents`

2. **Enter Arguments:**
   ```json
   {
     "query": "employee benefits",
     "department": "hr",
     "user_role": "HR Team",
     "top_k": 3
   }
   ```

3. **Click "Execute"**

4. **View Response:**
   ```json
   {
     "content": [
       {
         "type": "text",
         "text": "[Source 1: hr_policies.pdf] ...\n\n[Source 2: benefits_guide.pdf] ..."
       }
     ]
   }
   ```

5. **Check Protocol Tab:** See the actual JSON-RPC request/response

---

## Troubleshooting

### Inspector Can't Connect

**Error:** `Failed to connect to MCP server`

**Solutions:**
1. Verify backend is running: `http://localhost:8000/health`
2. Check MCP endpoint exists: `http://localhost:8000/mcp`
3. Ensure no CORS issues (should be configured in `main.py`)
4. Check console for errors (F12 in browser)

### Tools Not Appearing

**Check:**
1. MCP server started correctly (check backend logs)
2. Connection URL is exactly: `http://localhost:8000/mcp`
3. Transport is set to **Streamable HTTP** or **HTTP**

### Tool Execution Fails

**Check:**
1. Arguments are valid JSON
2. All required fields are provided
3. API keys are set in `.env`
4. Check backend logs for errors

---

## Advanced: Viewing Protocol Details

### JSON-RPC Request Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_documents",
    "arguments": {
      "query": "employee benefits",
      "department": "hr",
      "user_role": "HR Team",
      "top_k": 3
    }
  }
}
```

### JSON-RPC Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "..."
      }
    ],
    "isError": false
  }
}
```

---

## Verifying Your MCP Implementation

### Checklist:

- [ ] All 4 tools appear in Inspector
- [ ] Each tool shows correct parameters
- [ ] Tool execution returns results
- [ ] No JSON-RPC errors
- [ ] Protocol messages are valid
- [ ] RBAC works (test with different roles)

---

## Alternative Testing Methods

### 1. **Using cURL**
```powershell
curl -X POST http://localhost:8000/mcp `
  -H "Content-Type: application/json" `
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

### 2. **Using Python Script**
```python
import httpx
import asyncio

async def test_mcp():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        print(response.json())

asyncio.run(test_mcp())
```

### 3. **Using Postman**
```
POST http://localhost:8000/mcp
Content-Type: application/json

Body:
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

---

## Screenshots Expected

When you connect, you should see:

1. **Connection successful** indicator (green)
2. **4 tools listed:**
   - `search_documents`
   - `query_database`
   - `web_search`
   - `get_weather`
3. **Tool parameters** displayed for each
4. **JSON-RPC messages** in protocol viewer

---

## Resources

- **MCP Inspector Repo:** https://github.com/modelcontextprotocol/inspector
- **MCP Specification:** https://spec.modelcontextprotocol.io
- **Python SDK Docs:** https://github.com/modelcontextprotocol/python-sdk

---

## Quick Command Reference

```powershell
# Start Inspector (no install)
npx @modelcontextprotocol/inspector

# Install globally
npm install -g @modelcontextprotocol/inspector
mcp-inspector

# Test MCP endpoint
curl http://localhost:8000/mcp

# View backend health
curl http://localhost:8000/health
```

---

**Your MCP Server URL:** `http://localhost:8000/mcp`

**Transport:** Streamable HTTP

**Status:** ✅ Ready to inspect!
