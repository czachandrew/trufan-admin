#!/usr/bin/env python3
"""Seed test data for development and testing"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.venue import Venue
from app.models.parking import ParkingLot
from app.models.convenience import ConvenienceItem
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
            address={
                "street": "4 Pennsylvania Plaza",
                "city": "New York",
                "state": "NY",
                "zipCode": "10001",
                "country": "USA"
            },
            settings={
                "parkingEnabled": True,
                "valetEnabled": True,
                "convenienceStoreEnabled": True
            }
        )
        db.add(venue)
        db.flush()
        print(f"✅ Created venue: {venue.name}")

        # Create parking lots near major cities
        test_lots = [
            {
                "name": "MSG North Garage",
                "venue_id": venue.id,
                "capacity": 500,
                "available_spaces": 500,
                "location": {"latitude": 40.7505, "longitude": -73.9934},  # NYC
                "pricing": {"hourlyRate": "5.00", "dailyMax": "40.00", "eventRate": "25.00"},
                "is_public": True,
                "is_active": True,
                "address": {
                    "street": "350 W 31st St",
                    "city": "New York",
                    "state": "NY",
                    "zipCode": "10001"
                }
            },
            {
                "name": "Downtown LA Parking",
                "venue_id": venue.id,
                "capacity": 300,
                "available_spaces": 300,
                "location": {"latitude": 34.0522, "longitude": -118.2437},  # LA
                "pricing": {"hourlyRate": "6.00", "dailyMax": "45.00", "eventRate": "30.00"},
                "is_public": True,
                "is_active": True,
                "address": {
                    "street": "123 S Figueroa St",
                    "city": "Los Angeles",
                    "state": "CA",
                    "zipCode": "90012"
                }
            },
            {
                "name": "Chicago Loop Garage",
                "venue_id": venue.id,
                "capacity": 400,
                "available_spaces": 400,
                "location": {"latitude": 41.8781, "longitude": -87.6298},  # Chicago
                "pricing": {"hourlyRate": "4.50", "dailyMax": "35.00", "eventRate": "20.00"},
                "is_public": True,
                "is_active": True,
                "address": {
                    "street": "200 N Michigan Ave",
                    "city": "Chicago",
                    "state": "IL",
                    "zipCode": "60601"
                }
            },
            {
                "name": "SF Union Square Parking",
                "venue_id": venue.id,
                "capacity": 250,
                "available_spaces": 250,
                "location": {"latitude": 37.7875, "longitude": -122.4075},  # SF
                "pricing": {"hourlyRate": "7.00", "dailyMax": "50.00", "eventRate": "35.00"},
                "is_public": True,
                "is_active": True,
                "address": {
                    "street": "333 Post St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zipCode": "94108"
                }
            }
        ]

        for lot_data in test_lots:
            lot = ParkingLot(
                id=str(uuid.uuid4()),
                **lot_data
            )
            db.add(lot)
            print(f"✅ Created lot: {lot.name}")

        # Create convenience items (simple approach without categories/stores)
        items = [
            {
                "name": "Coca-Cola",
                "description": "12 oz can",
                "category": "beverage",
                "sku": "COKE-12",
                "base_price": "3.50",
                "markup_amount": "0.50",
                "final_price": "4.00",
                "source_store": "Walgreens"
            },
            {
                "name": "Water",
                "description": "16 oz bottle",
                "category": "beverage",
                "sku": "WATER-16",
                "base_price": "2.50",
                "markup_amount": "0.50",
                "final_price": "3.00",
                "source_store": "Walgreens"
            },
            {
                "name": "Chips",
                "description": "Assorted flavors",
                "category": "food",
                "sku": "CHIPS-1",
                "base_price": "4.00",
                "markup_amount": "0.50",
                "final_price": "4.50",
                "source_store": "Walgreens"
            },
            {
                "name": "Hot Dog",
                "description": "All beef with bun",
                "category": "food",
                "sku": "HOTDOG-1",
                "base_price": "6.00",
                "markup_amount": "0.50",
                "final_price": "6.50",
                "source_store": "Walgreens"
            }
        ]

        for item_data in items:
            item = ConvenienceItem(
                id=str(uuid.uuid4()),
                venue_id=venue.id,
                markup_percent=0,
                is_active=True,
                **item_data
            )
            db.add(item)
            print(f"✅ Created item: {item.name}")

        db.commit()
        print("\n✅ Test data seeded successfully!")
        print(f"\nVenue ID: {venue.id}")
        print(f"Store ID: {store.id}")
        print(f"Created {len(test_lots)} parking lots")
        print(f"Created {len(items)} inventory items")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
