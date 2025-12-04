"""
Database Configuration - SQLAlchemy with SQLite
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# SQLAlchemy Engine & Session
# =============================================================================
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True  # Verify connections before using
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =============================================================================
# Database Utilities
# =============================================================================
def init_database() -> None:
    """
    Initialize database - create all tables
    Call this on application startup
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session
    Automatically handles session lifecycle
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all_tables() -> None:
    """
    Drop all tables (use with caution!)
    Useful for testing or complete reset
    """
    logger.warning("⚠️ Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ All tables dropped")
