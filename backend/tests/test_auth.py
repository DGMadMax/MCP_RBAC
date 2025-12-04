"""
Unit Tests for Authentication & Authorization
"""

import pytest
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, verify_token
from app.models import User


class TestPasswordHashing:
    """Test password hashing utilities"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "mySecurePass123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testPassword456"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "correctPassword"
        wrong_password = "wrongPassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWT:
    """Test JWT token management"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user_id = 1
        role = "Engineering Team"
        department = "engineering"
        
        token = create_access_token(user_id, role, department)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token_valid(self):
        """Test JWT token verification with valid token"""
        user_id = 123
        role = "HR Team"
        department = "hr"
        
        token = create_access_token(user_id, role, department)
        payload = verify_token(token)
        
        assert payload["sub"] == str(user_id)
        assert payload["role"] == role
        assert payload["department"] == department
        assert "exp" in payload
    
    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token"""
        from jose import JWTError
        
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            verify_token(invalid_token)


class TestUserModel:
    """Test User database model"""
    
    def test_create_user(self, test_db):
        """Test user creation"""
        user = User(
            email="newuser@test.com",
            hashed_password=hash_password("password123"),
            full_name="New User",
            role="Finance Team",
            department="finance",
            is_active=True
        )
        
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@test.com"
        assert user.department == "finance"
        assert user.is_active is True
    
    def test_user_repr(self, test_user):
        """Test user string representation"""
        repr_str = repr(test_user)
        
        assert "test@example.com" in repr_str
        assert "Engineering Team" in repr_str
        assert "engineering" in repr_str
