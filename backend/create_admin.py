#!/usr/bin/env python3
"""
Create default admin user for Sean Picks
Run this after setting up PostgreSQL
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import engine, Base, SessionLocal
from app.models.user import User
from app.models.bet_tracking import Base as BetTrackingBase
from app.auth import get_password_hash

def create_admin_user():
    """Create default admin user"""
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    BetTrackingBase.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if admin exists
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@seanpicks.com",
            hashed_password=get_password_hash("seanpicks123"),
            bankroll=1000.0,
            unit_size=30.0,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created successfully!")
        print("Username: admin")
        print("Password: seanpicks123")
        print("⚠️  IMPORTANT: Change this password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()