"""
Centralized Logging - Production-Grade with Thread-Safe Queue
Uses Python's standard logging module (NOT Loguru)
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
from typing import Any, Dict, List, Optional

# =============================================================================
# Configuration
# =============================================================================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

CENTRAL_LOG_FILE = LOG_DIR / f"application_{datetime.now().strftime('%Y%m%d')}.log"
DEBUG_LOG_FILE = LOG_DIR / f"debug_{datetime.now().strftime('%Y%m%d')}.log"

log_queue: Queue = Queue(-1)
queue_listener: Optional[QueueListener] = None
_LOGGING_INITIALIZED = False


# =============================================================================
# Core Setup Functions
# =============================================================================
def setup_centralized_logging() -> None:
    """
    Initialize centralized logging with queue-based handlers
    Thread-safe logging using QueueHandler + QueueListener pattern
    """
    global _LOGGING_INITIALIZED, queue_listener

    if _LOGGING_INITIALIZED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # File handler (rotating) - Application logs
    file_handler = RotatingFileHandler(
        CENTRAL_LOG_FILE,
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | [%(threadName)-15s] | %(name)-25s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Debug file handler - RAG pipeline debugging
    debug_handler = RotatingFileHandler(
        DEBUG_LOG_FILE,
        maxBytes=50 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - [%(threadName)-12s] - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # Queue-based logging (thread-safe)
    queue_handler = QueueHandler(log_queue)
    root_logger.addHandler(queue_handler)

    queue_listener = QueueListener(
        log_queue,
        file_handler,
        debug_handler,
        console_handler,
        respect_handler_level=True
    )
    queue_listener.start()

    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    _LOGGING_INITIALIZED = True
    root_logger.info("=" * 80)
    root_logger.info(f"Centralized logging initialized - Log: {CENTRAL_LOG_FILE}")
    root_logger.info(f"Debug logs: {DEBUG_LOG_FILE}")
    root_logger.info("=" * 80)


def get_logger(module_name: str) -> logging.Logger:
    """
    Get logger for module
    
    Args:
        module_name: Name of the module (__name__)
    
    Returns:
        Logger instance
    """
    if not _LOGGING_INITIALIZED:
        setup_centralized_logging()
    return logging.getLogger(module_name)


def shutdown_logging() -> None:
    """
    Shutdown logging - call at application exit to flush
    """
    global queue_listener, _LOGGING_INITIALIZED
    if queue_listener:
        logging.info("Shutting down logging...")
        queue_listener.stop()
        queue_listener = None
        _LOGGING_INITIALIZED = False


# =============================================================================
# RAG Pipeline Debugging Helpers
# =============================================================================
def log_rag_debug(logger: logging.Logger, stage: str, data: Dict[str, Any]) -> None:
    """
    Log RAG pipeline debugging details in structured format
    
    Args:
        logger: Logger instance
        stage: Pipeline stage (e.g., "VECTOR_SEARCH", "RRF_FUSION")
        data: Debug data to log
    """
    logger.debug(f"[RAG-{stage}] {json.dumps(data, indent=2)}")


def log_llm_response(logger: logging.Logger, query: str, response: str, model: str) -> None:
    """
    Log every LLM response for debugging
    
    Args:
        logger: Logger instance
        query: User query
        response: LLM response
        model: Model name
    """
    logger.debug(
        f"[LLM-Response] Model={model} | "
        f"Query={query[:100]}{'...' if len(query) > 100 else ''} | "
        f"Response={response[:200]}{'...' if len(response) > 200 else ''}"
    )


def log_chunks(logger: logging.Logger, chunks: List[Dict[str, Any]], stage: str) -> None:
    """
    Log top 3 chunks with all scores (vector, BM25, RRF, rerank)
    
    Args:
        logger: Logger instance
        chunks: List of chunk dictionaries
        stage: Pipeline stage (e.g., "VECTOR", "BM25", "RRF", "RERANKED")
    """
    for i, chunk in enumerate(chunks[:3], 1):
        logger.debug(
            f"[CHUNK-{stage}-{i}] "
            f"VectorScore={chunk.get('vector_score', 'N/A')} | "
            f"BM25Score={chunk.get('bm25_score', 'N/A')} | "
            f"RRFScore={chunk.get('rrf_score', 'N/A')} | "
            f"RerankScore={chunk.get('rerank_score', 'N/A')} | "
            f"Text={chunk.get('text', chunk.get('content', ''))[:150]}..."
        )


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    query: str,
    result: Optional[Dict[str, Any]],
    duration_ms: float,
    success: bool = True
) -> None:
    """
    Log tool execution details
    
    Args:
        logger: Logger instance
        tool_name: Name of the tool (e.g., "RAG", "SQL", "Web", "Weather")
        query: Query sent to tool
        result: Tool execution result
        duration_ms: Execution duration in milliseconds
        success: Whether execution succeeded
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"[TOOL-{tool_name}] {status} | "
        f"Duration={duration_ms:.2f}ms | "
        f"Query={query[:100]}{'...' if len(query) > 100 else ''}"
    )
    if result:
        logger.debug(f"[TOOL-{tool_name}-RESULT] {json.dumps(result, indent=2)}")


def log_rbac_filter(
    logger: logging.Logger,
    user_role: str,
    user_department: str,
    allowed_departments: List[str],
    filtered_count: int
) -> None:
    """
    Log RBAC filtering results
    
    Args:
        logger: Logger instance
        user_role: User's role
        user_department: User's department
        allowed_departments: Departments user can access
        filtered_count: Number of documents after filtering
    """
    logger.debug(
        f"[RBAC-FILTER] Role={user_role} | "
        f"Department={user_department} | "
        f"AllowedDepts={allowed_departments} | "
        f"FilteredDocs={filtered_count}"
    )
