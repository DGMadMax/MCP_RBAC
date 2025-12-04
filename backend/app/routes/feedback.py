"""
Feedback Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import FeedbackRequest
from app.auth import get_current_user
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("")
async def submit_feedback(
    feedback: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a chat response
    """
    # In a real app, you would save this to a Feedback table
    # For now, we'll just log it
    logger.info(
        f"Feedback received from user {user.email}: "
        f"Helpful={feedback.helpful}, Rating={feedback.rating}, "
        f"Comment={feedback.comment}"
    )
    
    return {"success": True, "message": "Feedback received"}
