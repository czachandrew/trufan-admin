#!/usr/bin/env python3
"""
Associate Greenfield Plaza Parking lot with the lot owner user.
Run with: docker-compose exec api python -m scripts.associate_lot_with_owner
"""
import sys
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.parking import ParkingLot


def associate_lot():
    """Associate Greenfield lot with owner user."""
    db: Session = SessionLocal()

    try:
        print("\n" + "="*60)
        print("ASSOCIATING LOT WITH OWNER")
        print("="*60 + "\n")

        # Get the lot owner user
        owner = db.query(User).filter(User.email == "owner@greenfieldparking.com").first()
        if not owner:
            print("❌ Lot owner user not found!")
            print("   Run: docker-compose exec api python -m scripts.create_lot_owner")
            sys.exit(1)

        print(f"✓ Found lot owner user")
        print(f"  Email: {owner.email}")
        print(f"  ID: {owner.id}\n")

        # Get the Greenfield Plaza Parking lot
        lot = db.query(ParkingLot).filter(ParkingLot.name == "Greenfield Plaza Parking").first()
        if not lot:
            print("❌ Greenfield Plaza Parking lot not found!")
            sys.exit(1)

        print(f"✓ Found Greenfield Plaza Parking lot")
        print(f"  Name: {lot.name}")
        print(f"  ID: {lot.id}")
        print(f"  Current owner_id: {lot.owner_id}\n")

        # Associate the lot with the owner
        if lot.owner_id == owner.id:
            print("✓ Lot already associated with owner")
        else:
            lot.owner_id = owner.id
            db.commit()
            print(f"✓ Associated lot with owner")
            print(f"  Updated owner_id to: {owner.id}")

        print("\n" + "="*60)
        print("ASSOCIATION COMPLETE")
        print("="*60)
        print("\n✅ Greenfield Plaza Parking is now owned by owner@greenfieldparking.com")
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    associate_lot()
