#!/usr/bin/env python3
"""
Create an admin user for frontend testing.
Run with: docker-compose exec api python -m scripts.create_admin_user
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def create_admin_user():
    """Create admin user for frontend testing."""
    print("\n" + "="*60)
    print("CREATING ADMIN USER")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.email == "czachandrew@gmail.com"
        ).first()

        if existing_user:
            print(f"⚠️  User already exists!")
            print(f"   Email: {existing_user.email}")
            print(f"   ID: {existing_user.id}")
            print(f"   Role: {existing_user.role}")
            print(f"   Created: {existing_user.created_at}")

            # Update password
            print("\n   Updating password to 'password'...")
            existing_user.hashed_password = get_password_hash("password")
            db.commit()
            print("   ✓ Password updated!")

            return existing_user

        # Create new user
        print("Creating new admin user...")

        user = User(
            email="czachandrew@gmail.com",
            hashed_password=get_password_hash("password"),
            first_name="Andrew",
            last_name="Czachowski",
            role="super_admin",  # Super admin role for full access
            is_active=True,
            email_verified=True,  # Pre-verify for testing
            created_at=datetime.utcnow(),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("\n✅ Admin user created successfully!\n")
        print("User Details:")
        print(f"  Email: {user.email}")
        print(f"  ID: {user.id}")
        print(f"  Role: {user.role}")
        print(f"  First Name: {user.first_name}")
        print(f"  Last Name: {user.last_name}")
        print(f"  Email Verified: {user.email_verified}")
        print(f"  Active: {user.is_active}")
        print(f"  Created: {user.created_at}")

        print("\n" + "="*60)
        print("LOGIN CREDENTIALS")
        print("="*60)
        print(f"  Email: czachandrew@gmail.com")
        print(f"  Password: password")
        print("="*60 + "\n")

        print("You can now login at:")
        print("  POST http://localhost:8000/api/v1/auth/login")
        print("\n")

        return user

    except Exception as e:
        print(f"\n❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
