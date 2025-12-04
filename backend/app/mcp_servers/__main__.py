"""
MCP Servers Multi-Process Orchestrator
Runs all 4 MCP servers (RAG, SQL, Web, Weather) in parallel
"""

import multiprocessing
import uvicorn
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.logger import setup_centralized_logging, get_logger

setup_centralized_logging()
logger = get_logger(__name__)


def run_rag_server():
    """Run RAG MCP Server on port 8001"""
    from app.mcp_servers.rag_server import app
    logger.info("🔍 Starting RAG MCP Server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


def run_sql_server():
    """Run SQL MCP Server on port 8002"""
    from app.mcp_servers.sql_server import app
    logger.info("🗄️ Starting SQL MCP Server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")


def run_web_server():
    """Run Web Search MCP Server on port 8003"""
    from app.mcp_servers.web_server import app
    logger.info("🌐 Starting Web Search MCP Server on port 8003...")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")


def run_weather_server():
    """Run Weather MCP Server on port 8004"""
    from app.mcp_servers.weather_server import app
    logger.info("🌤️ Starting Weather MCP Server on port 8004...")
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🚀 Starting all MCP servers...")
    logger.info("=" * 80)
    
    # Create processes for each server
    processes = [
        multiprocessing.Process(target=run_rag_server, name="RAG-Server"),
        multiprocessing.Process(target=run_sql_server, name="SQL-Server"),
        multiprocessing.Process(target=run_web_server, name="Web-Server"),
        multiprocessing.Process(target=run_weather_server, name="Weather-Server"),
    ]
    
    # Start all processes
    for p in processes:
        p.start()
        logger.info(f"✓ Started {p.name} (PID: {p.pid})")
    
    logger.info("=" * 80)
    logger.info("✅ All MCP servers running!")
    logger.info("=" * 80)
    logger.info("Ports:")
    logger.info("  - RAG Server: http://localhost:8001")
    logger.info("  - SQL Server: http://localhost:8002")
    logger.info("  - Web Server: http://localhost:8003")
    logger.info("  - Weather Server: http://localhost:8004")
    logger.info("=" * 80)
    logger.info("Press Ctrl+C to stop all servers...")
    
    try:
        # Wait for all processes
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("\n⏹️ Shutting down all MCP servers...")
        for p in processes:
            p.terminate()
            p.join()
        logger.info("✅ All servers stopped")
