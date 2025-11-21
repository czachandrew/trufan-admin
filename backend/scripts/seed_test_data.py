#!/usr/bin/env python3
"""Seed test data for development and testing"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.venue import Venue
from app.models.parking import ParkingLot
from app.core.security import get_password_hash
import uuid

def seed_data():
    db = SessionLocal()
    try:
        print("🌱 Seeding test data...")

        # Create test venue
        venue = Venue(
            id=str(uuid.uuid4()),
            name="Madison Square Garden",
            slug="madison-square-garden",
            email="info@msg.com",
            phone="212-465-6741",
            address_line1="4 Pennsylvania Plaza",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA",
            configuration={
                "parkingEnabled": True,
                "valetEnabled": True,
                "convenienceStoreEnabled": True
            },
            is_active=True
        )
        db.add(venue)
        db.flush()
        print(f"✅ Created venue: {venue.name}")

        # Create parking lots near major cities
        test_lots = [
            {
                "name": "MSG North Garage",
                "venue_id": venue.id,
                "total_spaces": 500,
                "available_spaces": 500,
                "location_lat": 40.7505,
                "location_lng": -73.9934,
                "location_address": "350 W 31st St, New York, NY 10001",
                "pricing_config": {"hourly_rate": 5.00, "max_daily": 40.00, "base_rate": 0.00},
                "is_active": True
            },
            {
                "name": "Downtown LA Parking",
                "venue_id": venue.id,
                "total_spaces": 300,
                "available_spaces": 300,
                "location_lat": 34.0522,
                "location_lng": -118.2437,
                "location_address": "123 S Figueroa St, Los Angeles, CA 90012",
                "pricing_config": {"hourly_rate": 6.00, "max_daily": 45.00, "base_rate": 0.00},
                "is_active": True
            },
            {
                "name": "Chicago Loop Garage",
                "venue_id": venue.id,
                "total_spaces": 400,
                "available_spaces": 400,
                "location_lat": 41.8781,
                "location_lng": -87.6298,
                "location_address": "200 N Michigan Ave, Chicago, IL 60601",
                "pricing_config": {"hourly_rate": 4.50, "max_daily": 35.00, "base_rate": 0.00},
                "is_active": True
            },
            {
                "name": "SF Union Square Parking",
                "venue_id": venue.id,
                "total_spaces": 250,
                "available_spaces": 250,
                "location_lat": 37.7875,
                "location_lng": -122.4075,
                "location_address": "333 Post St, San Francisco, CA 94108",
                "pricing_config": {"hourly_rate": 7.00, "max_daily": 50.00, "base_rate": 0.00},
                "is_active": True
            }
        ]

        for lot_data in test_lots:
            lot = ParkingLot(
                id=str(uuid.uuid4()),
                **lot_data
            )
            db.add(lot)
            print(f"✅ Created lot: {lot.name}")

        # Skip convenience items for now - table doesn't exist yet
        # Requires database migration to create convenience_items table
        print("\n⏭️  Skipping convenience items (table not migrated yet)")

        db.commit()
        print("\n✅ Test data seeded successfully!")
        print(f"\nVenue ID: {venue.id}")
        print(f"Created {len(test_lots)} parking lots")
        print(f"\n💡 Tip: Your mobile app can now fetch these parking lots!")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
