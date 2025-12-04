"""
Pytest Fixtures and Configuration
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base
from app.models import User, Employee
from app.auth.password import hash_password
from app.main import app


# =============================================================================
# Database Fixtures
# =============================================================================
@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        role="Engineering Team",
        department="engineering",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin_user(test_db):
    """Create a test admin user (C-Level)"""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin User",
        role="C-Level",
        department="c-level",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_employee(test_db):
    """Create a test employee"""
    employee = Employee(
        employee_id="TEST001",
        full_name="Test Employee",
        role="Software Engineer",
        department="engineering",
        email="emp@test.com",
        salary=100000.0,
        leave_balance=15
    )
    test_db.add(employee)
    test_db.commit()
    test_db.refresh(employee)
    return employee


# =============================================================================
# API Client Fixtures
# =============================================================================
@pytest.fixture(scope="module")
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers with JWT token"""
    from app.auth.jwt import create_access_token
    
    token = create_access_token(
        user_id=test_user.id,
        role=test_user.role,
        department=test_user.department
    )
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user):
    """Generate auth headers for admin user"""
    from app.auth.jwt import create_access_token
    
    token = create_access_token(
        user_id=test_admin_user.id,
        role=test_admin_user.role,
        department=test_admin_user.department
    )
    
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Mock Data Fixtures
# =============================================================================
@pytest.fixture
def mock_rag_results():
    """Mock RAG search results"""
    return {
        "success": True,
        "results": [
            {
                "text": "FinSolve uses microservices architecture",
                "vector_score": 0.95,
                "bm25_score": 0.85,
                "rrf_score": 0.90,
                "rerank_score": 0.92,
                "metadata": {
                    "department": "engineering",
                    "file_name": "architecture.md"
                }
            },
            {
                "text": "Our tech stack includes Python, FastAPI, and PostgreSQL",
                "vector_score": 0.88,
                "bm25_score": 0.80,
                "rrf_score": 0.84,
                "rerank_score": 0.86,
                "metadata": {
                    "department": "engineering",
                    "file_name": "tech_stack.md"
                }
            }
        ],
        "metadata": {
            "query": "What is the architecture?",
            "total_time_ms": 150.5
        }
    }


@pytest.fixture
def mock_sql_results():
    """Mock SQL query results"""
    return {
        "success": True,
        "sql": "SELECT * FROM employees WHERE department = 'engineering'",
        "result": "| id | name | department |\n|---|---|---|\n| 1 | John | engineering |",
        "row_count": 1
    }


@pytest.fixture
def mock_web_results():
    """Mock web search results"""
    return {
        "success": True,
        "answer": "According to recent sources, Python 3.12 was released in October 2023.",
        "sources": ["https://docs.python.org/3.12/", "https://www.python.org/downloads/"],
        "query_time_ms": 850.0,
        "model_used": "llama-3.1-sonar-large-128k-online"
    }


@pytest.fixture
def mock_weather_results():
    """Mock weather results"""
    return {
        "success": True,
        "city": "Bangalore",
        "temperature": 24.5,
        "windspeed": 12.3,
        "formatted": "Weather in Bangalore: 24.5°C, Wind: 12.3 km/h"
    }
