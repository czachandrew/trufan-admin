#!/usr/bin/env python3
"""
Seed script to create test parking lots in Greenfield, WI and Grand Cayman.
Run with: python -m scripts.seed_test_lots
"""
import asyncio
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.parking import ParkingLot, ParkingSpace


def create_greenfield_lot(db: Session) -> ParkingLot:
    """Create test parking lot in Greenfield, Wisconsin."""

    # Greenfield coordinates (near Milwaukee)
    greenfield_lat = Decimal("42.9614")
    greenfield_lng = Decimal("-88.0126")

    lot = ParkingLot(
        name="Greenfield Plaza Parking",
        description="Convenient parking in downtown Greenfield. Close to shopping and dining.",
        location_address="5300 W Layton Ave, Greenfield, WI 53220",
        location_lat=greenfield_lat,
        location_lng=greenfield_lng,
        total_spaces=50,
        available_spaces=50,
        is_active=True,
        pricing_config={
            "base_rate": 5.00,
            "hourly_rate": 3.00,
            "max_daily_rate": 30.00,
            "min_duration_hours": 0.5,
            "dynamic_multiplier": 1.0,
        }
    )

    db.add(lot)
    db.flush()  # Get the lot ID

    # Create parking spaces
    spaces = []

    # Section A: Standard spaces (1-30)
    for i in range(1, 31):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"A-{i:03d}",
            space_type="standard",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    # Section B: Handicap spaces (1-5)
    for i in range(1, 6):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"B-{i:03d}",
            space_type="handicap",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    # Section C: EV charging spaces (1-10)
    for i in range(1, 11):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"C-{i:03d}",
            space_type="ev",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    # Section D: Valet spaces (1-5)
    for i in range(1, 6):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"D-{i:03d}",
            space_type="valet",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    db.add_all(spaces)
    db.commit()

    print(f"✓ Created Greenfield lot with {len(spaces)} spaces")
    print(f"  - Lot ID: {lot.id}")
    print(f"  - Location: {lot.location_address}")
    print(f"  - Coordinates: {lot.location_lat}, {lot.location_lng}")
    print(f"  - QR Code URL: trufan://parking/lot/{lot.id}")

    return lot


def create_grand_cayman_lot(db: Session) -> ParkingLot:
    """Create test parking lot in Grand Cayman."""

    # Grand Cayman coordinates (George Town)
    cayman_lat = Decimal("19.2866")
    cayman_lng = Decimal("-81.3744")

    lot = ParkingLot(
        name="Seven Mile Beach Parking",
        description="Beachfront parking near hotels and restaurants. Short walk to famous Seven Mile Beach.",
        location_address="West Bay Road, Seven Mile Beach, Grand Cayman",
        location_lat=cayman_lat,
        location_lng=cayman_lng,
        total_spaces=75,
        available_spaces=75,
        is_active=True,
        pricing_config={
            "base_rate": 8.00,  # CI$ (Cayman Islands Dollar)
            "hourly_rate": 5.00,
            "max_daily_rate": 50.00,
            "min_duration_hours": 1.0,
            "dynamic_multiplier": 1.2,  # Higher pricing for tourist area
        }
    )

    db.add(lot)
    db.flush()

    # Create parking spaces
    spaces = []

    # Beach Level: Standard spaces (1-40)
    for i in range(1, 41):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"BEACH-{i:03d}",
            space_type="standard",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    # Upper Level: Standard spaces (1-20)
    for i in range(1, 21):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"UPPER-{i:03d}",
            space_type="standard",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    # Handicap spaces (1-5)
    for i in range(1, 6):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"HC-{i:03d}",
            space_type="handicap",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    # Premium beachfront spaces (1-10)
    for i in range(1, 11):
        space = ParkingSpace(
            lot_id=lot.id,
            space_number=f"PREMIUM-{i:03d}",
            space_type="valet",
            is_occupied=False,
            is_active=True,
        )
        spaces.append(space)

    db.add_all(spaces)
    db.commit()

    print(f"✓ Created Grand Cayman lot with {len(spaces)} spaces")
    print(f"  - Lot ID: {lot.id}")
    print(f"  - Location: {lot.location_address}")
    print(f"  - Coordinates: {lot.location_lat}, {lot.location_lng}")
    print(f"  - QR Code URL: trufan://parking/lot/{lot.id}")

    return lot


def main():
    """Main function to seed test parking lots."""
    print("\n=== Seeding Test Parking Lots ===\n")

    db = SessionLocal()
    try:
        # Check if lots already exist
        existing_lots = db.query(ParkingLot).filter(
            ParkingLot.name.in_([
                "Greenfield Plaza Parking",
                "Seven Mile Beach Parking"
            ])
        ).all()

        if existing_lots:
            print(f"⚠ Found {len(existing_lots)} existing test lot(s)")
            print("  Run with --force to recreate (not implemented)")
            print("  Or manually delete from database first")
            return

        # Create lots
        greenfield_lot = create_greenfield_lot(db)
        print()
        cayman_lot = create_grand_cayman_lot(db)

        print("\n=== Seeding Complete ===\n")
        print("Test these lots with the following QR codes:")
        print(f"  Greenfield: trufan://parking/lot/{greenfield_lot.id}")
        print(f"  Grand Cayman: trufan://parking/lot/{cayman_lot.id}")
        print("\nOr test specific spaces:")
        print(f"  Greenfield Space A-001: trufan://parking/lot/{greenfield_lot.id}/space/A-001")
        print(f"  Grand Cayman Beach-001: trufan://parking/lot/{cayman_lot.id}/space/BEACH-001")
        print()

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding lots: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
