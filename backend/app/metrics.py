"""
Prometheus metrics definitions and middleware.
"""
from typing import Callable
import time

from prometheus_client import Counter, Histogram, Gauge, Info
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from logger import log_error

# Application info
app_info = Info("app", "Application information")
app_info.info({
    "version": "1.0.0",
    "service": "rbac-chatbot",
})

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"]
)

# Business metrics
queries_total = Counter(
    "queries_total",
    "Total user queries processed",
    ["department", "status"]
)

query_duration_seconds = Histogram(
    "query_duration_seconds",
    "Query processing duration",
    ["department"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

tool_calls_total = Counter(
    "tool_calls_total",
    "Total tool calls",
    ["tool", "status"]
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Track in-progress
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        
        except Exception as e:
            log_error("Request failed", exc_info=True)
            raise
        
        finally:
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()
