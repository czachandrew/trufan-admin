#!/usr/bin/env python3
"""
Add a few sample opportunities for testing the iOS frontend.
Run with: docker-compose exec api python -m scripts.add_sample_opportunities
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.opportunity import Partner, Opportunity


def create_sample_partner(db):
    """Create a sample partner or use existing one."""
    # Check if we already have a test partner
    partner = db.query(Partner).filter(
        Partner.api_key == "pk_sample_test_key_999"
    ).first()

    if partner:
        print(f"✓ Using existing sample partner: {partner.business_name}")
        return partner

    # Create new sample partner (use Greenfield, WI location for easy testing)
    partner = Partner(
        business_name="Main Street Coffee Co.",
        business_type="cafe",
        contact_email="hello@mainstreetcoffee.com",
        contact_phone="+14145551234",
        address="123 Main Street, Greenfield, WI 53220",
        location_lat=Decimal("42.9614"),  # Greenfield, WI
        location_lng=Decimal("-88.0126"),
        api_key="pk_sample_test_key_999",
        commission_rate=Decimal("0.12"),
        auto_approve_opportunities=True,
        is_active=True,
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    print(f"✓ Created sample partner: {partner.business_name}")
    return partner


def create_sample_opportunities(db, partner):
    """Create 2-3 compelling sample opportunities."""

    now = datetime.utcnow()
    opportunities = []

    # Opportunity 1: Morning Coffee Deal
    # Perfect for testing morning discovery
    opp1 = Opportunity(
        partner_id=partner.id,
        title="☕ Free Pastry with Any Coffee",
        value_proposition="Buy any coffee, get a fresh pastry free! Perfect way to start your day.",
        opportunity_type="discovery",
        trigger_rules={
            "time_remaining_min": 20,
            "time_remaining_max": 90,
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "time_of_day_start": "06:00",
            "time_of_day_end": "11:00",
        },
        value_details={
            "fixed_value_usd": 4.50,
            "perks": ["fresh_baked", "artisan_coffee"],
            "parking_extension_minutes": 15,
        },
        valid_from=now,
        valid_until=now + timedelta(days=60),
        total_capacity=200,
        used_capacity=23,  # Some already claimed
        priority_score=75,
        location_lat=partner.location_lat,
        location_lng=partner.location_lng,
        address=partner.address,
        walking_distance_meters=120,
        is_active=True,
        is_approved=True,
        created_at=now,
    )
    opportunities.append(opp1)

    # Opportunity 2: Lunch Special
    # Great for midday testing
    opp2 = Opportunity(
        partner_id=partner.id,
        title="🍔 $8 Lunch Special",
        value_proposition="Gourmet burger, fries, and a drink for just $8. Usually $14!",
        opportunity_type="bundle",
        trigger_rules={
            "time_remaining_min": 30,
            "time_remaining_max": 120,
            "time_of_day_start": "11:00",
            "time_of_day_end": "14:30",
        },
        value_details={
            "discount_fixed_amount": 6.00,
            "original_price": 14.00,
            "perks": ["includes_drink", "fast_service"],
            "parking_extension_minutes": 30,
        },
        valid_from=now,
        valid_until=now + timedelta(days=45),
        total_capacity=100,
        used_capacity=12,
        priority_score=85,
        location_lat=partner.location_lat,
        location_lng=partner.location_lng,
        address=partner.address,
        walking_distance_meters=120,
        is_active=True,
        is_approved=True,
        created_at=now,
    )
    opportunities.append(opp2)

    # Opportunity 3: Afternoon Pick-Me-Up
    # Flexible timing for testing
    opp3 = Opportunity(
        partner_id=partner.id,
        title="☀️ 25% Off Afternoon Treats",
        value_proposition="Get 25% off any specialty drink or dessert between 2-5pm",
        opportunity_type="convenience",
        trigger_rules={
            "time_remaining_min": 25,
            "time_remaining_max": 180,
            "time_of_day_start": "14:00",
            "time_of_day_end": "17:00",
        },
        value_details={
            "discount_percentage": 25,
            "perks": ["happy_hour_special", "outdoor_seating"],
            "parking_extension_minutes": 20,
        },
        valid_from=now,
        valid_until=now + timedelta(days=90),
        total_capacity=None,  # Unlimited
        used_capacity=0,
        priority_score=70,
        location_lat=partner.location_lat,
        location_lng=partner.location_lng,
        address=partner.address,
        walking_distance_meters=120,
        is_active=True,
        is_approved=True,
        created_at=now,
    )
    opportunities.append(opp3)

    # Add all to database
    for opp in opportunities:
        db.add(opp)

    db.commit()

    return opportunities


def main():
    """Create sample opportunities for testing."""
    print("\n" + "="*60)
    print("ADDING SAMPLE OPPORTUNITIES FOR TESTING")
    print("="*60 + "\n")

    db = SessionLocal()

    try:
        # Create partner
        partner = create_sample_partner(db)

        # Create opportunities
        print("\nCreating sample opportunities...")
        opportunities = create_sample_opportunities(db, partner)

        print(f"\n✅ Successfully created {len(opportunities)} sample opportunities!\n")

        # Display created opportunities
        print("Sample Opportunities Created:")
        print("-" * 60)
        for idx, opp in enumerate(opportunities, 1):
            print(f"\n{idx}. {opp.title}")
            print(f"   ID: {opp.id}")
            print(f"   Type: {opp.opportunity_type}")
            print(f"   Value: {opp.value_proposition}")
            print(f"   Parking Extension: {opp.value_details.get('parking_extension_minutes')} min")
            print(f"   Capacity: {opp.used_capacity}/{opp.total_capacity or '∞'}")
            print(f"   Priority Score: {opp.priority_score}")

        print("\n" + "-" * 60)
        print("\nℹ️  Testing Information:")
        print(f"   Partner: {partner.business_name}")
        print(f"   API Key: {partner.api_key}")
        print(f"   Location: Greenfield, WI (42.9614, -88.0126)")
        print("\n   To test these opportunities:")
        print("   1. Create a parking session at the Greenfield lot")
        print("   2. Call GET /api/v1/opportunities/active?session_id={session_id}")
        print("   3. You should see these opportunities in the response")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error creating sample opportunities: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
