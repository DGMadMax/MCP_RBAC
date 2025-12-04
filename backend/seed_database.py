"""
Database Seeding Script - Create Demo Users for Testing
Run this once to populate database with test users for each role
"""

import asyncio
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_database
from app.models import User
from app.auth.password import hash_password
from app.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Demo Users Configuration
# =============================================================================
DEMO_USERS = [
    {
        "email": "admin@test.com",
        "password": "admin123",  # CHANGE IN PRODUCTION!
        "full_name": "Admin User",
        "role": "C-Level",
        "department": "c-level"
    },
    {
        "email": "engineering@test.com",
        "password": "eng123",
        "full_name": "Engineering User",
        "role": "Engineering Team",
        "department": "engineering"
    },
    {
        "email": "finance@test.com",
        "password": "fin123",
        "full_name": "Finance User",
        "role": "Finance Team",
        "department": "finance"
    },
    {
        "email": "hr@test.com",
        "password": "hr123",
        "full_name": "HR User",
        "role": "HR Team",
        "department": "hr"
    },
    {
        "email": "marketing@test.com",
        "password": "mkt123",
        "full_name": "Marketing User",
        "role": "Marketing Team",
        "department": "marketing"
    },
    {
        "email": "employee@test.com",
        "password": "emp123",
        "full_name": "General Employee",
        "role": "Employee",
        "department": "general"
    },
]


def seed_users(db: Session) -> None:
    """
    Seed database with demo users
    
    Args:
        db: Database session
    """
    logger.info("=" * 80)
    logger.info("Seeding demo users...")
    logger.info("=" * 80)
    
    created_count = 0
    skipped_count = 0
    
    for user_data in DEMO_USERS:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            logger.info(f"✓ User already exists: {user_data['email']} (skipping)")
            skipped_count += 1
            continue
        
        # Create new user
        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            department=user_data["department"],
            is_active=True
        )
        
        db.add(user)
        logger.info(
            f"✓ Created user: {user_data['email']} | "
            f"Role: {user_data['role']} | "
            f"Department: {user_data['department']}"
        )
        created_count += 1
    
    db.commit()
    
    logger.info("=" * 80)
    logger.info(f"Seeding complete! Created: {created_count}, Skipped: {skipped_count}")
    logger.info("=" * 80)
    
    if created_count > 0:
        logger.info("\n📝 Demo User Credentials:")
        logger.info("-" * 80)
        for user_data in DEMO_USERS:
            logger.info(f"  {user_data['email']:<25} | Password: {user_data['password']}")
        logger.info("-" * 80)


def main():
    """Main execution"""
    # Initialize database tables
    init_database()
    
    # Seed users
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
