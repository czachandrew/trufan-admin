#!/usr/bin/env python3
"""
Create a single lot owner account with their parking lot in Greenfield, WI.
Run with: docker-compose exec api python -m scripts.create_lot_owner
"""
import sys
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.parking import ParkingLot


def create_lot_owner():
    """Create a lot owner user and their parking lot."""
    db: Session = SessionLocal()

    try:
        print("\n" + "="*60)
        print("CREATING LOT OWNER ACCOUNT")
        print("="*60 + "\n")

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "owner@greenfieldparking.com").first()

        if existing_user:
            print(f"⚠️  User already exists: owner@greenfieldparking.com")
            user = existing_user
            print(f"   Using existing user ID: {user.id}")
        else:
            # Create lot owner user
            print("Step 1: Creating lot owner user...")
            user = User(
                email="owner@greenfieldparking.com",
                hashed_password=get_password_hash("password"),
                first_name="John",
                last_name="Greenfield",
                role="venue_admin",  # Lot owner/operator role
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow(),
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            print(f"✓ Created user account")
            print(f"  Email: owner@greenfieldparking.com")
            print(f"  Password: password")
            print(f"  Role: venue_admin")
            print(f"  ID: {user.id}\n")

        # Create parking lot in Greenfield
        print("Step 2: Creating parking lot in Greenfield, WI...")

        lot = ParkingLot(
            name="Greenfield Plaza Parking",
            description="Convenient parking for Greenfield Plaza shops and restaurants",
            location_address="5300 W Layton Ave, Greenfield, WI 53220",
            total_spaces=75,
            available_spaces=75,
            location_lat=Decimal("42.9614"),
            location_lng=Decimal("-88.0126"),
            pricing_config={
                "base_rate": 5.00,
                "hourly_rate": 3.00,
                "max_daily": 25.00,
                "min_duration_minutes": 15,
                "max_duration_hours": 24,
                "dynamic_multiplier": 1.0,
            },
            is_active=True,
            venue_id=None,  # Simple lot owner, no complex venue structure
        )

        db.add(lot)
        db.commit()
        db.refresh(lot)

        print(f"✓ Created parking lot")
        print(f"  Name: {lot.name}")
        print(f"  Address: {lot.location_address}")
        print(f"  Total Spaces: {lot.total_spaces}")
        print(f"  Hourly Rate: ${lot.pricing_config['hourly_rate']}")
        print(f"  Max Daily: ${lot.pricing_config['max_daily']}")
        print(f"  ID: {lot.id}\n")

        print("="*60)
        print("LOT OWNER SETUP COMPLETE")
        print("="*60)
        print("\n✅ Login Credentials:")
        print(f"   Email: owner@greenfieldparking.com")
        print(f"   Password: password")
        print(f"\n✅ Parking Lot:")
        print(f"   Name: Greenfield Plaza Parking")
        print(f"   Location: Greenfield, WI")
        print(f"   Spaces: 75")
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_lot_owner()
