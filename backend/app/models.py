"""
Database Models - SQLAlchemy ORM Models
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    User model for authentication and RBAC
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # RBAC fields
    role = Column(String(100), nullable=False)  # e.g., "Engineering Team", "C-Level"
    department = Column(String(100), nullable=False)  # e.g., "engineering", "finance"
    
    # Status & timestamps
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email={self.email}, role={self.role}, department={self.department})>"


class ChatHistory(Base):
    """
    Chat history model to store conversation messages
    """
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Message content
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Metadata
    tools_used = Column(JSON)  # e.g., ["rag", "sql"]
    sources = Column(JSON)  # e.g., [{"file": "doc.md", "department": "engineering"}]
    intent = Column(String(50))  # e.g., "rag", "sql", "greeting"
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")
    
    def __repr__(self):
        return f"<ChatHistory(user_id={self.user_id}, query={self.query[:50]}...)>"


class Employee(Base):
    """
    Employee model (loaded from hr_data.csv)
    Used by SQL MCP server for structured queries
    """
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    role = Column(String(100), index=True)
    department = Column(String(100), index=True)
    email = Column(String(255))
    location = Column(String(100))
    
    # Dates
    date_of_birth = Column(Date)
    date_of_joining = Column(Date)
    
    # Organizational
    manager_id = Column(String(50))
    
    # Compensation & Performance
    salary = Column(Float, index=True)
    leave_balance = Column(Integer)
    leaves_taken = Column(Integer)
    attendance_pct = Column(Float)
    performance_rating = Column(Integer)
    last_review_date = Column(Date)
    
    def __repr__(self):
        return f"<Employee(employee_id={self.employee_id}, name={self.full_name}, dept={self.department})>"
