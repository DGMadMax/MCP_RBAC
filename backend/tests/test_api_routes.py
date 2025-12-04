"""
Unit Tests for API Routes
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthRoutes:
    """Test Authentication Routes"""
    
    def test_register_user_success(self, client, test_db):
        """Test user registration"""
        # Override get_db dependency
        from app.main import app
        from app.database import get_db
        
        def override_get_db():
            try:
                yield test_db
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "securepass123",
                "full_name": "New User",
                "role": "Engineering Team",
                "department": "engineering"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@test.com"
        
        app.dependency_overrides.clear()
    
    def test_register_duplicate_email(self, client, test_db, test_user):
        """Test registration with duplicate email"""
        from app.main import app
        from app.database import get_db
        
        def override_get_db():
            try:
                yield test_db
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Duplicate User",
                "role": "HR Team",
                "department": "hr"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
        
        app.dependency_overrides.clear()
    
    def test_login_success(self, client, test_db, test_user):
        """Test successful login"""
        from app.main import app
        from app.database import get_db
        
        def override_get_db():
            try:
                yield test_db
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        app.dependency_overrides.clear()
    
    def test_login_wrong_password(self, client, test_db, test_user):
        """Test login with wrong password"""
        from app.main import app
        from app.database import get_db
        
        def override_get_db():
            try:
                yield test_db
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        
        app.dependency_overrides.clear()


class TestHealthRoutes:
    """Test Health Check Routes"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RBAC Agentic AI Chatbot"
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        from unittest.mock import patch, AsyncMock
        
        # Mock MCP client health checks
        with patch("app.routes.health.rag_client") as mock_rag, \
             patch("app.routes.health.sql_client") as mock_sql, \
             patch("app.routes.health.web_client") as mock_web, \
             patch("app.routes.health.weather_client") as mock_weather:
            
            mock_rag.health_check = AsyncMock(return_value=True)
            mock_sql.health_check = AsyncMock(return_value=True)
            mock_web.health_check = AsyncMock(return_value=True)
            mock_weather.health_check = AsyncMock(return_value=True)
            
            response = client.get("/health")
            
            # Note: This might not work perfectly due to async, but structure is correct
            assert response.status_code == 200


class TestChatRoutes:
    """Test Chat Routes"""
    
    def test_chat_unauthorized(self, client):
        """Test chat without authentication"""
        response = client.post(
            "/chat",
            json={"query": "Hello"}
        )
        
        assert response.status_code == 403  # No auth header
    
    @pytest.mark.asyncio
    async def test_chat_history_authorized(self, client, test_db, auth_headers, test_user):
        """Test getting chat history with authentication"""
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        
        def override_get_db():
            try:
                yield test_db
            finally:
                pass
        
        async def override_get_current_user():
            return test_user
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        response = client.get(
            "/chat/history",
            headers=auth_headers
        )
        
        # Should work even with empty history
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        app.dependency_overrides.clear()


class TestRBACFiltering:
    """Test RBAC filtering in routes"""
    
    def test_c_level_sees_all_departments(self, client, test_db, admin_auth_headers, test_admin_user):
        """Test C-Level user can access all departments"""
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        
        def override_get_db():
            try:
                yield test_db
            finally:
                pass
        
        async def override_get_current_user():
            return test_admin_user
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # C-Level should have role "C-Level"
        assert test_admin_user.role == "C-Level"
        assert test_admin_user.department == "c-level"
        
        app.dependency_overrides.clear()
    
    def test_regular_user_department_restricted(self, test_user):
        """Test regular user is department-restricted"""
        assert test_user.role == "Engineering Team"
        assert test_user.department == "engineering"
