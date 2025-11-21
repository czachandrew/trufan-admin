"""
Basic tests for opportunity models and database setup.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.opportunity import (
    Partner,
    Opportunity,
    OpportunityInteraction,
    OpportunityPreferences,
    OpportunityType,
    InteractionType,
    FrequencyPreference,
)
from app.models.user import User


class TestOpportunityModels:
    """Test opportunity model creation and relationships."""

    def test_create_partner(self, db):
        """Test creating a partner."""
        partner = Partner(
            business_name="Test Restaurant",
            business_type="restaurant",
            contact_email="test@restaurant.com",
            contact_phone="555-0100",
            address="123 Main St",
            location_lat=Decimal("19.2866"),
            location_lng=Decimal("-81.3744"),
            api_key="test_key_12345",
            commission_rate=Decimal("0.15"),
            max_active_opportunities=10,
            is_active=True,
        )

        db.add(partner)
        db.commit()
        db.refresh(partner)

        assert partner.id is not None
        assert partner.business_name == "Test Restaurant"
        assert partner.commission_rate == Decimal("0.15")
        assert partner.is_active is True

    def test_create_opportunity(self, db, test_partner):
        """Test creating an opportunity."""
        opportunity = Opportunity(
            partner_id=test_partner.id,
            title="20% Off Dinner",
            value_proposition="Get 20% off your entire bill",
            opportunity_type=OpportunityType.EXPERIENCE.value,
            trigger_rules={
                "time_remaining_min": 30,
                "time_remaining_max": 120,
            },
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30),
            total_capacity=50,
            used_capacity=0,
            value_details={
                "discount_percentage": 20,
                "perks": ["skip_line"],
            },
            location_lat=Decimal("19.2866"),
            location_lng=Decimal("-81.3744"),
            address="123 Main St",
            is_active=True,
            is_approved=True,
        )

        db.add(opportunity)
        db.commit()
        db.refresh(opportunity)

        assert opportunity.id is not None
        assert opportunity.partner_id == test_partner.id
        assert opportunity.title == "20% Off Dinner"
        assert opportunity.opportunity_type == OpportunityType.EXPERIENCE.value
        assert opportunity.value_details["discount_percentage"] == 20
        assert opportunity.is_available is True

    def test_opportunity_availability(self, db, test_partner):
        """Test opportunity availability property."""
        # Available opportunity
        available_opp = Opportunity(
            partner_id=test_partner.id,
            title="Available Opportunity",
            value_proposition="Test",
            opportunity_type=OpportunityType.EXPERIENCE.value,
            trigger_rules={},
            valid_from=datetime.utcnow() - timedelta(hours=1),
            valid_until=datetime.utcnow() + timedelta(hours=1),
            total_capacity=10,
            used_capacity=5,
            value_details={"discount_percentage": 10},
            is_active=True,
            is_approved=True,
        )

        assert available_opp.is_available is True

        # At capacity
        available_opp.used_capacity = 10
        assert available_opp.is_available is False

        # Not active
        available_opp.used_capacity = 5
        available_opp.is_active = False
        assert available_opp.is_available is False

        # Expired
        available_opp.is_active = True
        available_opp.valid_until = datetime.utcnow() - timedelta(hours=1)
        assert available_opp.is_available is False

    def test_create_interaction(self, db, test_user, test_opportunity, test_parking_session):
        """Test creating an opportunity interaction."""
        interaction = OpportunityInteraction(
            user_id=test_user.id,
            opportunity_id=test_opportunity.id,
            parking_session_id=test_parking_session.id,
            interaction_type=InteractionType.ACCEPTED.value,
            interaction_context={
                "parking_time_remaining": 45,
                "distance_from_opportunity": 150,
            },
            value_claimed=test_opportunity.value_details,
            created_at=datetime.utcnow(),
        )

        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        assert interaction.id is not None
        assert interaction.user_id == test_user.id
        assert interaction.opportunity_id == test_opportunity.id
        assert interaction.interaction_type == InteractionType.ACCEPTED.value
        assert interaction.interaction_context["parking_time_remaining"] == 45

    def test_create_preferences(self, db, test_user):
        """Test creating user preferences."""
        preferences = OpportunityPreferences(
            user_id=test_user.id,
            opportunities_enabled=True,
            frequency_preference=FrequencyPreference.OCCASIONAL.value,
            max_per_session=3,
            quiet_hours=[{"start": "22:00", "end": "08:00"}],
            no_opportunity_days=["sunday"],
            preferred_categories=["experience", "convenience"],
            blocked_categories=[],
            blocked_partner_ids=[],
            max_walking_distance_meters=500,
            acceptance_patterns={},
        )

        db.add(preferences)
        db.commit()
        db.refresh(preferences)

        assert preferences.user_id == test_user.id
        assert preferences.opportunities_enabled is True
        assert preferences.frequency_preference == FrequencyPreference.OCCASIONAL.value
        assert preferences.max_walking_distance_meters == 500
        assert "sunday" in preferences.no_opportunity_days

    def test_partner_opportunity_relationship(self, db, test_partner):
        """Test relationship between partner and opportunities."""
        # Create multiple opportunities
        for i in range(3):
            opp = Opportunity(
                partner_id=test_partner.id,
                title=f"Opportunity {i}",
                value_proposition="Test",
                opportunity_type=OpportunityType.EXPERIENCE.value,
                trigger_rules={},
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=30),
                value_details={"discount_percentage": 10},
                is_active=True,
                is_approved=True,
            )
            db.add(opp)

        db.commit()
        db.refresh(test_partner)

        assert len(test_partner.opportunities) == 3

    def test_user_interaction_relationship(self, db, test_user, test_opportunity, test_parking_session):
        """Test relationship between user and interactions."""
        # Create multiple interactions
        for interaction_type in [InteractionType.IMPRESSED, InteractionType.VIEWED, InteractionType.ACCEPTED]:
            interaction = OpportunityInteraction(
                user_id=test_user.id,
                opportunity_id=test_opportunity.id,
                parking_session_id=test_parking_session.id,
                interaction_type=interaction_type.value,
                interaction_context={},
                created_at=datetime.utcnow(),
            )
            db.add(interaction)

        db.commit()
        db.refresh(test_user)

        assert len(test_user.opportunity_interactions) == 3


# Fixtures

@pytest.fixture
def test_partner(db):
    """Create a test partner."""
    partner = Partner(
        business_name="Test Partner",
        business_type="restaurant",
        contact_email="partner@test.com",
        api_key="test_api_key",
        is_active=True,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@pytest.fixture
def test_opportunity(db, test_partner):
    """Create a test opportunity."""
    opportunity = Opportunity(
        partner_id=test_partner.id,
        title="Test Opportunity",
        value_proposition="Test value proposition",
        opportunity_type=OpportunityType.EXPERIENCE.value,
        trigger_rules={},
        valid_from=datetime.utcnow() - timedelta(hours=1),
        valid_until=datetime.utcnow() + timedelta(hours=24),
        total_capacity=100,
        used_capacity=0,
        value_details={"discount_percentage": 20},
        is_active=True,
        is_approved=True,
    )
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@pytest.fixture
def test_parking_session(db, test_user):
    """Create a test parking session."""
    from app.models.parking import ParkingSession, ParkingLot

    # Create a test lot
    lot = ParkingLot(
        name="Test Lot",
        description="Test parking lot",
        total_spaces=100,
        available_spaces=100,
        location_lat=Decimal("19.2866"),
        location_lng=Decimal("-81.3744"),
        is_active=True,
        pricing_config={
            "base_rate": 5.00,
            "hourly_rate": 3.00,
            "max_daily": 30.00,
        }
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)

    session = ParkingSession(
        lot_id=lot.id,
        user_id=test_user.id,
        vehicle_plate="TEST123",
        vehicle_make="Toyota",
        vehicle_model="Camry",
        vehicle_color="Silver",
        start_time=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=2),
        base_price=Decimal("11.00"),
        status="active",
        access_code="TESTCODE",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
