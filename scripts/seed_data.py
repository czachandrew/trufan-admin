#!/usr/bin/env python3
"""
Seed script for populating the database with sample data.

Run this script to create sample users, venues, events, and other data for development.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.venue import Venue, VenueStaff
from app.models.event import Event, EventStatus
from app.models.parking import ParkingLot, ParkingStatus


def create_users(db: Session) -> dict:
    """Create sample users."""
    print("Creating users...")

    users = {
        "admin": User(
            id=uuid.uuid4(),
            email="admin@trufan.com",
            phone="+15551234567",
            hashed_password=get_password_hash("Admin123!"),
            first_name="Admin",
            last_name="User",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
            email_verified=True,
            phone_verified=True,
        ),
        "venue_admin": User(
            id=uuid.uuid4(),
            email="venue.admin@example.com",
            phone="+15551234568",
            hashed_password=get_password_hash("VenueAdmin123!"),
            first_name="Venue",
            last_name="Admin",
            role=UserRole.VENUE_ADMIN,
            is_active=True,
            is_verified=True,
            email_verified=True,
            phone_verified=True,
        ),
        "venue_staff": User(
            id=uuid.uuid4(),
            email="staff@example.com",
            phone="+15551234569",
            hashed_password=get_password_hash("Staff123!"),
            first_name="Staff",
            last_name="Member",
            role=UserRole.VENUE_STAFF,
            is_active=True,
            is_verified=True,
            email_verified=True,
            phone_verified=True,
        ),
        "customer1": User(
            id=uuid.uuid4(),
            email="customer1@example.com",
            phone="+15551234570",
            hashed_password=get_password_hash("Customer123!"),
            first_name="John",
            last_name="Doe",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
            email_verified=True,
            phone_verified=True,
        ),
        "customer2": User(
            id=uuid.uuid4(),
            email="customer2@example.com",
            phone="+15551234571",
            hashed_password=get_password_hash("Customer123!"),
            first_name="Jane",
            last_name="Smith",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
            email_verified=True,
            phone_verified=True,
        ),
    }

    for user in users.values():
        db.add(user)

    db.commit()
    print(f"Created {len(users)} users")
    return users


def create_venues(db: Session, users: dict) -> dict:
    """Create sample venues."""
    print("Creating venues...")

    venues = {
        "madison_square": Venue(
            id=uuid.uuid4(),
            name="Madison Square Garden",
            slug="madison-square-garden",
            email="info@msg.com",
            phone="+12125551000",
            address_line1="4 Pennsylvania Plaza",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA",
            is_active=True,
            description="World-famous arena in the heart of Manhattan",
            website="https://www.msg.com",
            configuration={
                "timezone": "America/New_York",
                "currency": "USD",
                "capacity": 20000,
                "features": ["parking", "concessions", "merchandise"],
            },
        ),
        "staples_center": Venue(
            id=uuid.uuid4(),
            name="Crypto.com Arena",
            slug="crypto-arena",
            email="info@cryptoarena.com",
            phone="+12135551000",
            address_line1="1111 S Figueroa St",
            city="Los Angeles",
            state="CA",
            zip_code="90015",
            country="USA",
            is_active=True,
            description="Premier sports and entertainment venue in LA",
            website="https://www.cryptoarena.com",
            configuration={
                "timezone": "America/Los_Angeles",
                "currency": "USD",
                "capacity": 19000,
                "features": ["parking", "concessions", "merchandise", "vip"],
            },
        ),
    }

    for venue in venues.values():
        db.add(venue)

    db.commit()

    # Add staff to venues
    venue_staff = [
        VenueStaff(
            user_id=users["venue_admin"].id,
            venue_id=venues["madison_square"].id,
            role="admin",
            is_active=True,
            permissions={"all": True},
        ),
        VenueStaff(
            user_id=users["venue_staff"].id,
            venue_id=venues["madison_square"].id,
            role="staff",
            is_active=True,
            permissions={"scan_tickets": True, "manage_parking": True},
        ),
    ]

    for staff in venue_staff:
        db.add(staff)

    db.commit()
    print(f"Created {len(venues)} venues")
    return venues


def create_events(db: Session, venues: dict) -> dict:
    """Create sample events."""
    print("Creating events...")

    now = datetime.utcnow()
    events = {
        "concert": Event(
            id=uuid.uuid4(),
            venue_id=venues["madison_square"].id,
            name="Summer Music Festival 2024",
            slug="summer-music-festival-2024",
            description="The biggest music festival of the summer featuring top artists",
            start_time=now + timedelta(days=30),
            end_time=now + timedelta(days=30, hours=6),
            doors_open=now + timedelta(days=30, hours=-1),
            total_capacity=15000,
            available_tickets=15000,
            base_price=99.99,
            status=EventStatus.PUBLISHED.value,
            configuration={
                "ticket_types": [
                    {"name": "general", "price": 99.99, "quantity": 10000},
                    {"name": "vip", "price": 299.99, "quantity": 1000},
                    {"name": "premium", "price": 499.99, "quantity": 500},
                ],
                "age_restriction": 18,
            },
        ),
        "basketball": Event(
            id=uuid.uuid4(),
            venue_id=venues["madison_square"].id,
            name="NBA Championship Game",
            slug="nba-championship-2024",
            description="Experience the excitement of championship basketball",
            start_time=now + timedelta(days=45),
            end_time=now + timedelta(days=45, hours=3),
            doors_open=now + timedelta(days=45, hours=-2),
            total_capacity=18000,
            available_tickets=18000,
            base_price=149.99,
            status=EventStatus.PUBLISHED.value,
            configuration={
                "ticket_types": [
                    {"name": "upper_deck", "price": 149.99, "quantity": 8000},
                    {"name": "lower_bowl", "price": 299.99, "quantity": 7000},
                    {"name": "courtside", "price": 999.99, "quantity": 100},
                ],
            },
        ),
    }

    for event in events.values():
        db.add(event)

    db.commit()
    print(f"Created {len(events)} events")
    return events


def create_parking_lots(db: Session, venues: dict) -> dict:
    """Create sample parking lots."""
    print("Creating parking lots...")

    parking_lots = {
        "lot_a": ParkingLot(
            id=uuid.uuid4(),
            venue_id=venues["madison_square"].id,
            name="Parking Lot A - North",
            description="Main parking lot on north side",
            total_spaces=500,
            available_spaces=500,
            location_lat=40.750504,
            location_lng=-73.993439,
            is_active=True,
            pricing_config={
                "base_rate": 30.00,
                "hourly_rate": 10.00,
                "max_daily": 80.00,
                "dynamic_multiplier": 1.0,
                "event_multiplier": 1.5,
            },
        ),
        "lot_b": ParkingLot(
            id=uuid.uuid4(),
            venue_id=venues["madison_square"].id,
            name="Parking Lot B - VIP",
            description="Premium VIP parking with covered spaces",
            total_spaces=100,
            available_spaces=100,
            location_lat=40.751504,
            location_lng=-73.993439,
            is_active=True,
            pricing_config={
                "base_rate": 50.00,
                "hourly_rate": 15.00,
                "max_daily": 150.00,
                "dynamic_multiplier": 1.0,
                "event_multiplier": 2.0,
            },
        ),
    }

    for lot in parking_lots.values():
        db.add(lot)

    db.commit()
    print(f"Created {len(parking_lots)} parking lots")
    return parking_lots


def main():
    """Run the seed script."""
    print("Starting database seeding...")
    print("-" * 50)

    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    try:
        # Create sample data
        users = create_users(db)
        venues = create_venues(db, users)
        events = create_events(db, venues)
        parking_lots = create_parking_lots(db, venues)

        print("-" * 50)
        print("Database seeding completed successfully!")
        print("\nSample login credentials:")
        print("  Super Admin: admin@trufan.com / Admin123!")
        print("  Venue Admin: venue.admin@example.com / VenueAdmin123!")
        print("  Staff: staff@example.com / Staff123!")
        print("  Customer 1: customer1@example.com / Customer123!")
        print("  Customer 2: customer2@example.com / Customer123!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
