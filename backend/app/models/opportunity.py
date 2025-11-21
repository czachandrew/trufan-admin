from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Boolean, Index, Text, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class OpportunityType(str, enum.Enum):
    """Types of opportunities that can be offered."""
    EXPERIENCE = "experience"
    CONVENIENCE = "convenience"
    DISCOVERY = "discovery"
    SERVICE = "service"
    BUNDLE = "bundle"


class InteractionType(str, enum.Enum):
    """Types of user interactions with opportunities."""
    IMPRESSED = "impressed"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class FrequencyPreference(str, enum.Enum):
    """User's frequency preference for opportunities."""
    ALL = "all"
    OCCASIONAL = "occasional"
    MINIMAL = "minimal"


class Partner(Base):
    """Partners are businesses offering opportunities to users."""

    __tablename__ = "partners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Business information
    business_name = Column(String(200), nullable=False)
    business_type = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    location_lat = Column(Numeric(10, 8), nullable=True)
    location_lng = Column(Numeric(11, 8), nullable=True)

    # Integration details
    webhook_url = Column(Text, nullable=True)
    api_key = Column(String(255), unique=True, nullable=True, index=True)

    # Settlement/billing
    stripe_account_id = Column(String(255), nullable=True)
    commission_rate = Column(Numeric(3, 2), nullable=False, default=0.15)
    billing_email = Column(String(255), nullable=True)

    # Settings
    auto_approve_opportunities = Column(Boolean, default=False, nullable=False)
    max_active_opportunities = Column(Integer, default=10, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    opportunities = relationship("Opportunity", back_populates="partner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Partner {self.business_name}>"


class Opportunity(Base):
    """
    Opportunities are value moments offered to users based on their context.
    These are NOT ads - they are genuine value propositions.
    """

    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    partner_id = Column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core value proposition
    title = Column(String(100), nullable=False)
    value_proposition = Column(Text, nullable=False)
    opportunity_type = Column(String(20), nullable=False)

    # Trigger conditions (when should this appear)
    trigger_rules = Column(JSONB, nullable=False, default={})
    # Example: {"parking_duration_min": 60, "time_remaining_min": 15, "days_of_week": ["friday"]}

    # Availability window
    valid_from = Column(DateTime, nullable=False, index=True)
    valid_until = Column(DateTime, nullable=False, index=True)
    availability_schedule = Column(JSONB, nullable=True)

    # Capacity management
    total_capacity = Column(Integer, nullable=True)
    used_capacity = Column(Integer, default=0, nullable=False)

    # Value details
    value_details = Column(JSONB, nullable=False)
    # Example: {"discount_percentage": 20, "parking_extension_minutes": 30, "perks": []}

    # Location data
    location_lat = Column(Numeric(10, 8), nullable=True)
    location_lng = Column(Numeric(11, 8), nullable=True)
    address = Column(Text, nullable=True)
    walking_distance_meters = Column(Integer, nullable=True)

    # Configuration
    max_impressions_per_user = Column(Integer, default=3, nullable=False)
    cooldown_hours = Column(Integer, default=24, nullable=False)
    priority_score = Column(Integer, default=50, nullable=False)

    # State
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    partner = relationship("Partner", back_populates="opportunities")
    interactions = relationship("OpportunityInteraction", back_populates="opportunity", cascade="all, delete-orphan")
    analytics = relationship("OpportunityAnalytics", back_populates="opportunity", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_opportunities_active', 'is_active', 'is_approved'),
        Index('ix_opportunities_location', 'location_lat', 'location_lng'),
        Index('ix_opportunities_valid_dates', 'valid_from', 'valid_until'),
        CheckConstraint('valid_until > valid_from', name='valid_date_range'),
        CheckConstraint('used_capacity <= total_capacity OR total_capacity IS NULL', name='valid_capacity'),
    )

    def __repr__(self):
        return f"<Opportunity {self.title}>"

    @property
    def is_available(self) -> bool:
        """Check if opportunity is currently available."""
        now = datetime.utcnow()
        has_capacity = self.total_capacity is None or self.used_capacity < self.total_capacity
        is_valid = self.valid_from <= now <= self.valid_until
        return self.is_active and self.is_approved and has_capacity and is_valid


class OpportunityInteraction(Base):
    """
    Track all user interactions with opportunities.
    This is essential for analytics and learning user preferences.
    """

    __tablename__ = "opportunity_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    parking_session_id = Column(UUID(as_uuid=True), ForeignKey("parking_sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    interaction_type = Column(String(20), nullable=False)

    # Context when interaction happened
    interaction_context = Column(JSONB, nullable=True)
    # Example: {"parking_time_remaining": 35, "distance_from_opportunity": 150, "weather": "clear"}

    # Value tracking
    value_claimed = Column(JSONB, nullable=True)
    value_redeemed = Column(JSONB, nullable=True)
    partner_revenue = Column(Numeric(10, 2), nullable=True)
    platform_commission = Column(Numeric(10, 2), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="opportunity_interactions")
    opportunity = relationship("Opportunity", back_populates="interactions")
    parking_session = relationship("ParkingSession")

    # Indexes
    __table_args__ = (
        Index('ix_interactions_user', 'user_id', 'created_at'),
        Index('ix_interactions_session', 'parking_session_id'),
    )

    def __repr__(self):
        return f"<OpportunityInteraction {self.interaction_type} - {self.id}>"


class OpportunityPreferences(Base):
    """
    User preferences for opportunity discovery.
    Gives users full control over what they see and when.
    """

    __tablename__ = "opportunity_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Master control
    opportunities_enabled = Column(Boolean, default=True, nullable=False)

    # Frequency control
    frequency_preference = Column(String(20), default='occasional', nullable=False)
    max_per_session = Column(Integer, default=3, nullable=False)

    # Timing preferences
    quiet_hours = Column(JSONB, default=[], nullable=False)  # [{"start": "22:00", "end": "08:00"}]
    no_opportunity_days = Column(ARRAY(String(10)), default=[], nullable=False)  # ['sunday', 'monday']

    # Category preferences
    preferred_categories = Column(ARRAY(String(20)), default=[], nullable=False)
    blocked_categories = Column(ARRAY(String(20)), default=[], nullable=False)
    blocked_partner_ids = Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)

    # Location preferences
    max_walking_distance_meters = Column(Integer, default=500, nullable=False)

    # Learning data (private, never shared)
    acceptance_patterns = Column(JSONB, default={}, nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="opportunity_preferences")

    def __repr__(self):
        return f"<OpportunityPreferences for user {self.user_id}>"


class OpportunityAnalytics(Base):
    """
    Analytics for partners.
    Focuses on value metrics, not traditional ad metrics.
    """

    __tablename__ = "opportunity_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    hour = Column(Integer, nullable=True)  # 0-23 for hourly breakdowns, NULL for daily

    # Exposure metrics (we track but don't charge for these)
    unique_impressions = Column(Integer, default=0, nullable=False)
    total_impressions = Column(Integer, default=0, nullable=False)

    # Engagement metrics (what matters)
    views = Column(Integer, default=0, nullable=False)  # Clicked for details
    acceptances = Column(Integer, default=0, nullable=False)  # User claimed it
    completions = Column(Integer, default=0, nullable=False)  # Actually redeemed

    # Value metrics
    total_user_value = Column(Numeric(10, 2), default=0.00, nullable=False)  # Sum of discounts/perks
    total_partner_revenue = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_platform_commission = Column(Numeric(10, 2), default=0.00, nullable=False)

    # Performance metrics
    avg_time_to_accept = Column(Integer, nullable=True)  # Seconds from impression to accept
    avg_distance_meters = Column(Integer, nullable=True)  # Avg distance of accepting users

    # Relationships
    opportunity = relationship("Opportunity", back_populates="analytics")

    # Indexes
    __table_args__ = (
        Index('ix_analytics_date', 'opportunity_id', 'date'),
    )

    def __repr__(self):
        return f"<OpportunityAnalytics {self.date} - {self.opportunity_id}>"
