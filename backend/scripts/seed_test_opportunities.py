#!/usr/bin/env python3
"""
Seed script to create test partners and opportunities.
Run with: docker-compose exec api python -m scripts.seed_test_opportunities
"""
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.opportunity import Partner, Opportunity


def create_test_partners(db):
    """Create test partners in both locations."""

    partners = []

    # Partner 1: Restaurant in Grand Cayman
    partner1 = Partner(
        business_name="Cayman Beach Grill",
        business_type="restaurant",
        contact_email="owner@caymanbeachgrill.com",
        contact_phone="+1-345-555-0100",
        address="West Bay Road, Seven Mile Beach, Grand Cayman",
        location_lat=Decimal("19.2866"),
        location_lng=Decimal("-81.3744"),
        api_key="pk_cayman_beach_test_key_12345",
        webhook_url="https://caymanbeachgrill.com/api/webhooks/trufan",
        billing_email="billing@caymanbeachgrill.com",
        commission_rate=Decimal("0.15"),
        auto_approve_opportunities=True,  # Skip approval for testing
        max_active_opportunities=20,
        is_active=True,
    )
    db.add(partner1)
    partners.append(partner1)

    # Partner 2: Coffee shop in Greenfield, WI
    partner2 = Partner(
        business_name="Greenfield Cafe & Roasters",
        business_type="cafe",
        contact_email="hello@greenfieldcafe.com",
        contact_phone="+1-414-555-0200",
        address="5280 W Layton Ave, Greenfield, WI 53220",
        location_lat=Decimal("42.9614"),
        location_lng=Decimal("-88.0126"),
        api_key="pk_greenfield_cafe_test_key_67890",
        webhook_url="https://greenfieldcafe.com/api/webhooks/trufan",
        billing_email="accounting@greenfieldcafe.com",
        commission_rate=Decimal("0.12"),
        auto_approve_opportunities=True,
        max_active_opportunities=15,
        is_active=True,
    )
    db.add(partner2)
    partners.append(partner2)

    # Partner 3: Retail shop in Grand Cayman
    partner3 = Partner(
        business_name="Island Treasures Gift Shop",
        business_type="retail",
        contact_email="info@islandtreasures.ky",
        contact_phone="+1-345-555-0300",
        address="Harbour Drive, George Town, Grand Cayman",
        location_lat=Decimal("19.2920"),
        location_lng=Decimal("-81.3700"),
        api_key="pk_island_treasures_test_key_abc123",
        billing_email="finance@islandtreasures.ky",
        commission_rate=Decimal("0.18"),
        auto_approve_opportunities=True,
        max_active_opportunities=10,
        is_active=True,
    )
    db.add(partner3)
    partners.append(partner3)

    db.commit()

    for partner in partners:
        db.refresh(partner)
        print(f"✓ Created partner: {partner.business_name}")
        print(f"  - Partner ID: {partner.id}")
        print(f"  - API Key: {partner.api_key}")
        print(f"  - Location: {partner.location_lat}, {partner.location_lng}")

    return partners


def create_test_opportunities(db, partners):
    """Create test opportunities for each partner."""

    opportunities = []

    # Cayman Beach Grill Opportunities
    cayman_restaurant = partners[0]

    # Opportunity 1: Dinner discount (evening, Friday/Saturday)
    opp1 = Opportunity(
        partner_id=cayman_restaurant.id,
        title="20% Off Dinner",
        value_proposition="Get 20% off your entire dinner bill plus free appetizer",
        opportunity_type="experience",
        trigger_rules={
            "time_remaining_min": 30,
            "time_remaining_max": 180,
            "days_of_week": ["friday", "saturday", "sunday"],
            "time_of_day_start": "17:00",
            "time_of_day_end": "22:00",
        },
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=60),
        total_capacity=100,
        used_capacity=0,
        value_details={
            "discount_percentage": 20,
            "perks": ["free_appetizer", "priority_seating"],
            "parking_extension_minutes": 30,
        },
        location_lat=cayman_restaurant.location_lat,
        location_lng=cayman_restaurant.location_lng,
        address=cayman_restaurant.address,
        walking_distance_meters=150,
        max_impressions_per_user=3,
        cooldown_hours=24,
        priority_score=85,
        is_active=True,
        is_approved=True,
    )
    db.add(opp1)
    opportunities.append(opp1)

    # Opportunity 2: Happy hour special
    opp2 = Opportunity(
        partner_id=cayman_restaurant.id,
        title="Happy Hour: 2-for-1 Drinks",
        value_proposition="Buy one drink, get one free during happy hour",
        opportunity_type="convenience",
        trigger_rules={
            "time_remaining_min": 45,
            "time_remaining_max": 120,
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "time_of_day_start": "16:00",
            "time_of_day_end": "18:30",
        },
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=90),
        total_capacity=50,
        used_capacity=12,  # Some already claimed
        value_details={
            "discount_percentage": 50,
            "perks": ["happy_hour_special"],
        },
        location_lat=cayman_restaurant.location_lat,
        location_lng=cayman_restaurant.location_lng,
        address=cayman_restaurant.address,
        walking_distance_meters=150,
        max_impressions_per_user=5,
        cooldown_hours=12,
        priority_score=70,
        is_active=True,
        is_approved=True,
    )
    db.add(opp2)
    opportunities.append(opp2)

    # Greenfield Cafe Opportunities
    greenfield_cafe = partners[1]

    # Opportunity 3: Morning coffee deal
    opp3 = Opportunity(
        partner_id=greenfield_cafe.id,
        title="Free Pastry with Coffee",
        value_proposition="Buy any coffee, get a free pastry of your choice",
        opportunity_type="discovery",
        trigger_rules={
            "time_remaining_min": 20,
            "time_remaining_max": 90,
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "time_of_day_start": "06:00",
            "time_of_day_end": "10:00",
        },
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=30),
        total_capacity=200,
        used_capacity=45,
        value_details={
            "discount_amount": 5,
            "perks": ["free_pastry"],
            "parking_extension_minutes": 15,
        },
        location_lat=greenfield_cafe.location_lat,
        location_lng=greenfield_cafe.location_lng,
        address=greenfield_cafe.address,
        walking_distance_meters=100,
        max_impressions_per_user=3,
        cooldown_hours=48,
        priority_score=75,
        is_active=True,
        is_approved=True,
    )
    db.add(opp3)
    opportunities.append(opp3)

    # Opportunity 4: Lunch bundle
    opp4 = Opportunity(
        partner_id=greenfield_cafe.id,
        title="Lunch Bundle: $10 Off",
        value_proposition="Get $10 off any lunch combo meal",
        opportunity_type="bundle",
        trigger_rules={
            "time_remaining_min": 30,
            "time_remaining_max": 120,
            "time_of_day_start": "11:00",
            "time_of_day_end": "14:00",
        },
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=45),
        total_capacity=None,  # Unlimited
        used_capacity=0,
        value_details={
            "discount_amount": 10,
            "perks": ["combo_meal"],
        },
        location_lat=greenfield_cafe.location_lat,
        location_lng=greenfield_cafe.location_lng,
        address=greenfield_cafe.address,
        walking_distance_meters=100,
        max_impressions_per_user=2,
        cooldown_hours=24,
        priority_score=80,
        is_active=True,
        is_approved=True,
    )
    db.add(opp4)
    opportunities.append(opp4)

    # Island Treasures Opportunities
    gift_shop = partners[2]

    # Opportunity 5: Shopping discount
    opp5 = Opportunity(
        partner_id=gift_shop.id,
        title="15% Off Everything",
        value_proposition="Get 15% off your entire purchase, no exclusions",
        opportunity_type="discovery",
        trigger_rules={
            "time_remaining_min": 30,
            "time_remaining_max": 240,
        },
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=14),
        total_capacity=75,
        used_capacity=8,
        value_details={
            "discount_percentage": 15,
            "perks": ["free_gift_wrap"],
        },
        location_lat=gift_shop.location_lat,
        location_lng=gift_shop.location_lng,
        address=gift_shop.address,
        walking_distance_meters=300,
        max_impressions_per_user=2,
        cooldown_hours=72,
        priority_score=60,
        is_active=True,
        is_approved=True,
    )
    db.add(opp5)
    opportunities.append(opp5)

    db.commit()

    for opp in opportunities:
        db.refresh(opp)
        print(f"\n✓ Created opportunity: {opp.title}")
        print(f"  - Opportunity ID: {opp.id}")
        print(f"  - Partner: {opp.partner.business_name}")
        print(f"  - Type: {opp.opportunity_type}")
        print(f"  - Value: {opp.value_proposition}")
        print(f"  - Capacity: {opp.used_capacity}/{opp.total_capacity or 'unlimited'}")

    return opportunities


def main():
    """Main function to seed test opportunities."""
    print("\n=== Seeding Test Partners and Opportunities ===\n")

    db = SessionLocal()
    try:
        # Check if test data already exists
        from app.models.opportunity import Partner
        existing = db.query(Partner).filter(
            Partner.api_key.like("pk_%_test_key_%")
        ).count()

        if existing > 0:
            print(f"⚠ Found {existing} existing test partner(s)")
            print("  Delete them manually if you want to recreate test data")
            return

        # Create test data
        partners = create_test_partners(db)
        print()
        opportunities = create_test_opportunities(db, partners)

        print("\n=== Seeding Complete ===\n")
        print("Test Partners Created:")
        for p in partners:
            print(f"  - {p.business_name}: {p.api_key}")

        print(f"\nTotal Opportunities Created: {len(opportunities)}")
        print("\nYou can now test the Opportunity Engine!")
        print("\nNext steps:")
        print("  1. Create a parking session for a user")
        print("  2. Query GET /api/v1/opportunities/active?session_id={session_id}")
        print("  3. Accept an opportunity")
        print("  4. Use partner API to validate and complete")
        print()

    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
