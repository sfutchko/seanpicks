"""
User management router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()

class BankrollUpdate(BaseModel):
    bankroll: float

class PreferencesUpdate(BaseModel):
    preferences: dict

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "bankroll": current_user.bankroll,
        "unit_size": current_user.unit_size,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at
    }

@router.put("/bankroll")
async def update_bankroll(
    update: BankrollUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user bankroll"""
    current_user.bankroll = update.bankroll
    current_user.unit_size = update.bankroll * 0.02  # 2% default unit size
    db.commit()
    
    return {
        "message": "Bankroll updated",
        "bankroll": current_user.bankroll,
        "unit_size": current_user.unit_size
    }

@router.put("/preferences")
async def update_preferences(
    update: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    current_user.preferences = update.preferences
    db.commit()
    
    return {
        "message": "Preferences updated",
        "preferences": current_user.preferences
    }