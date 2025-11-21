from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ValetStatus(str, enum.Enum):
    """Valet session status."""
    PENDING = "pending"
    CHECKED_IN = "checked_in"
    PARKED = "parked"
    RETRIEVAL_REQUESTED = "retrieval_requested"
    RETRIEVING = "retrieving"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceType(str, enum.Enum):
    """Type of valet service."""
    STANDARD = "standard"
    VIP = "vip"
    EVENT = "event"
    PREMIUM = "premium"


class IncidentType(str, enum.Enum):
    """Type of incident."""
    DAMAGE = "damage"
    DELAY = "delay"
    LOST_ITEM = "lost_item"
    COMPLAINT = "complaint"
    OTHER = "other"


class IncidentSeverity(str, enum.Enum):
    """Severity of incident."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationType(str, enum.Enum):
    """Type of communication."""
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"


class CommunicationStatus(str, enum.Enum):
    """Status of communication."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class ValetSession(Base):
    """Main valet session model for tracking valet parking usage."""

    __tablename__ = "valet_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    attendant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    saved_vehicle_id = Column(UUID(as_uuid=True), ForeignKey("saved_vehicles.id", ondelete="SET NULL"), nullable=True)

    # Vehicle information
    vehicle_plate = Column(String(20), nullable=False, index=True)
    vehicle_make = Column(String(50), nullable=True)
    vehicle_model = Column(String(50), nullable=True)
    vehicle_color = Column(String(30), nullable=True)
    vehicle_year = Column(Integer, nullable=True)
    vehicle_notes = Column(Text, nullable=True)

    # Service information
    service_type = Column(String(20), default=ServiceType.STANDARD.value, nullable=False)
    ticket_number = Column(String(20), nullable=False, unique=True, index=True)

    # Session timing
    check_in_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    parked_time = Column(DateTime, nullable=True)
    retrieval_requested_time = Column(DateTime, nullable=True)
    ready_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)

    # Estimated times
    estimated_retrieval_time = Column(DateTime, nullable=True)
    estimated_ready_time = Column(DateTime, nullable=True)

    # Pricing
    base_price = Column(Numeric(10, 2), nullable=False)
    service_fee = Column(Numeric(10, 2), default=0, nullable=False)
    tip_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    pricing_tier = Column(String(50), nullable=True)

    # Location/parking information
    parking_location = Column(String(100), nullable=True)  # e.g., "Lot A - Row 3"
    parking_space_id = Column(UUID(as_uuid=True), ForeignKey("parking_spaces.id", ondelete="SET NULL"), nullable=True)

    # Contact information
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)

    # Notifications
    notify_via_sms = Column(Boolean, default=True, nullable=False)
    notify_via_push = Column(Boolean, default=True, nullable=False)
    last_notification_sent = Column(DateTime, nullable=True)

    # Status and metadata
    status = Column(String(30), default=ValetStatus.PENDING.value, nullable=False, index=True)
    special_instructions = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    feedback = Column(Text, nullable=True)

    # Additional metadata
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Key management
    key_tag_number = Column(String(10), nullable=True, index=True)  # Numeric tag 001-999
    key_storage_zone = Column(String(50), nullable=True)
    key_storage_box = Column(String(50), nullable=True)
    key_storage_position = Column(String(20), nullable=True)
    key_status = Column(String(20), nullable=True)  # with_customer, with_valet, in_storage, grabbed, returned
    key_photo_url = Column(Text, nullable=True)
    key_notes = Column(Text, nullable=True)

    # Key tracking
    key_assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    key_assigned_at = Column(DateTime, nullable=True)
    key_grabbed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    key_grabbed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue", foreign_keys=[venue_id])
    user = relationship("User", foreign_keys=[user_id])
    attendant = relationship("User", foreign_keys=[attendant_id])
    saved_vehicle = relationship("SavedVehicle", back_populates="sessions")
    parking_space = relationship("ParkingSpace")
    status_events = relationship("ValetStatusEvent", back_populates="session", cascade="all, delete-orphan")
    communications = relationship("ValetCommunication", back_populates="session", cascade="all, delete-orphan")
    incidents = relationship("ValetIncident", back_populates="session", cascade="all, delete-orphan")
    key_assigned_by = relationship("User", foreign_keys=[key_assigned_by_id])
    key_grabbed_by = relationship("User", foreign_keys=[key_grabbed_by_id])

    # Indexes
    __table_args__ = (
        Index('ix_valet_sessions_venue_status', 'venue_id', 'status'),
        Index('ix_valet_sessions_user_status', 'user_id', 'status'),
        Index('ix_valet_sessions_attendant', 'attendant_id'),
        Index('ix_valet_sessions_check_in_time', 'check_in_time'),
        Index('ix_valet_sessions_ticket_number', 'ticket_number'),
        Index('ix_valet_sessions_key_tag_number', 'key_tag_number'),
    )

    def __repr__(self):
        return f"<ValetSession {self.ticket_number} - {self.vehicle_plate}>"


class ValetStatusEvent(Base):
    """Timeline/audit log of status changes for valet sessions."""

    __tablename__ = "valet_status_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("valet_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Status change information
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)

    # Location of status change (for mobile attendants)
    location_lat = Column(Numeric(10, 8), nullable=True)
    location_lng = Column(Numeric(11, 8), nullable=True)

    # Additional context
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    session = relationship("ValetSession", back_populates="status_events")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('ix_valet_status_events_session_created', 'session_id', 'created_at'),
        Index('ix_valet_status_events_new_status', 'new_status'),
    )

    def __repr__(self):
        return f"<ValetStatusEvent {self.session_id} - {self.old_status} -> {self.new_status}>"


class ValetCommunication(Base):
    """Log of SMS/push notifications sent to users."""

    __tablename__ = "valet_communications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("valet_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Communication details
    communication_type = Column(String(20), nullable=False)  # sms, push, email
    recipient = Column(String(255), nullable=False)  # phone number or email
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)

    # Status and delivery
    status = Column(String(20), default=CommunicationStatus.PENDING.value, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Provider information (e.g., Twilio message SID)
    provider_id = Column(String(100), nullable=True)
    provider_status = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Additional context
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    session = relationship("ValetSession", back_populates="communications")
    user = relationship("User")

    # Indexes
    __table_args__ = (
        Index('ix_valet_communications_session_type', 'session_id', 'communication_type'),
        Index('ix_valet_communications_status', 'status'),
        Index('ix_valet_communications_sent_at', 'sent_at'),
    )

    def __repr__(self):
        return f"<ValetCommunication {self.communication_type} - {self.recipient}>"


class ValetIncident(Base):
    """Incident reports for valet service (damages, delays, complaints)."""

    __tablename__ = "valet_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("valet_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Incident information
    incident_type = Column(String(20), nullable=False, index=True)
    severity = Column(String(20), default=IncidentSeverity.LOW.value, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Resolution
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Financial impact
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    actual_cost = Column(Numeric(10, 2), nullable=True)

    # Media attachments (URLs to photos, videos)
    attachments = Column(ARRAY(String), nullable=True, default=[])

    # Status
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    requires_followup = Column(Boolean, default=False, nullable=False)

    # Additional context
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("ValetSession", back_populates="incidents")
    venue = relationship("Venue")
    reporter = relationship("User", foreign_keys=[reporter_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

    # Indexes
    __table_args__ = (
        Index('ix_valet_incidents_session_type', 'session_id', 'incident_type'),
        Index('ix_valet_incidents_venue_severity', 'venue_id', 'severity'),
        Index('ix_valet_incidents_resolved', 'is_resolved'),
        Index('ix_valet_incidents_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ValetIncident {self.incident_type} - {self.title}>"


class ValetCapacity(Base):
    """Real-time capacity tracking for valet service."""

    __tablename__ = "valet_capacity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)

    # Capacity information
    total_capacity = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, default=0, nullable=False)
    available_capacity = Column(Integer, nullable=False)
    reserved_capacity = Column(Integer, default=0, nullable=False)

    # Staffing
    attendants_on_duty = Column(Integer, default=0, nullable=False)
    attendants_required = Column(Integer, nullable=True)

    # Performance metrics
    average_retrieval_time = Column(Integer, nullable=True)  # in minutes
    average_wait_time = Column(Integer, nullable=True)  # in minutes

    # Queue information
    pending_check_ins = Column(Integer, default=0, nullable=False)
    pending_retrievals = Column(Integer, default=0, nullable=False)

    # Status
    is_accepting_vehicles = Column(Boolean, default=True, nullable=False)
    status_message = Column(String(255), nullable=True)

    # Additional context
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue")

    # Indexes
    __table_args__ = (
        Index('ix_valet_capacity_venue', 'venue_id', unique=True),
        Index('ix_valet_capacity_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<ValetCapacity venue={self.venue_id} - {self.current_occupancy}/{self.total_capacity}>"


class SavedVehicle(Base):
    """User's saved vehicles for faster check-in."""

    __tablename__ = "saved_vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Vehicle information
    vehicle_plate = Column(String(20), nullable=False, index=True)
    vehicle_make = Column(String(50), nullable=False)
    vehicle_model = Column(String(50), nullable=False)
    vehicle_color = Column(String(30), nullable=False)
    vehicle_year = Column(Integer, nullable=True)

    # Additional details
    nickname = Column(String(50), nullable=True)  # e.g., "My BMW"
    special_instructions = Column(Text, nullable=True)

    # Photos (URLs)
    photos = Column(ARRAY(String), nullable=True, default=[])

    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    sessions = relationship("ValetSession", back_populates="saved_vehicle")

    # Indexes
    __table_args__ = (
        Index('ix_saved_vehicles_user_plate', 'user_id', 'vehicle_plate', unique=True),
        Index('ix_saved_vehicles_user_default', 'user_id', 'is_default'),
    )

    def __repr__(self):
        return f"<SavedVehicle {self.vehicle_make} {self.vehicle_model} - {self.vehicle_plate}>"


class ValetPricing(Base):
    """Pricing configuration for valet service by venue."""

    __tablename__ = "valet_pricing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)

    # Pricing tiers
    pricing_tier = Column(String(50), nullable=False)  # standard, vip, premium, event

    # Base pricing
    base_price = Column(Numeric(10, 2), nullable=False)
    service_fee = Column(Numeric(10, 2), default=0, nullable=False)

    # Time-based pricing
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    daily_max = Column(Numeric(10, 2), nullable=True)

    # Dynamic pricing
    surge_multiplier = Column(Numeric(4, 2), default=1.0, nullable=False)
    peak_hours_multiplier = Column(Numeric(4, 2), default=1.0, nullable=False)

    # Time windows (stored as JSONB for flexibility)
    # Example: {"monday": [{"start": "17:00", "end": "23:00", "multiplier": 1.5}]}
    peak_hours_config = Column(JSONB, nullable=True, default={})

    # Special event pricing
    event_pricing_enabled = Column(Boolean, default=False, nullable=False)
    event_multiplier = Column(Numeric(4, 2), default=1.0, nullable=False)

    # Status and validity
    is_active = Column(Boolean, default=True, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # Additional configuration
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue")

    # Indexes
    __table_args__ = (
        Index('ix_valet_pricing_venue_tier', 'venue_id', 'pricing_tier', unique=True),
        Index('ix_valet_pricing_active', 'is_active'),
    )

    def __repr__(self):
        return f"<ValetPricing venue={self.venue_id} tier={self.pricing_tier}>"


class ValetMetricsDaily(Base):
    """Daily aggregated metrics for valet service."""

    __tablename__ = "valet_metrics_daily"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_date = Column(DateTime, nullable=False, index=True)

    # Volume metrics
    total_sessions = Column(Integer, default=0, nullable=False)
    completed_sessions = Column(Integer, default=0, nullable=False)
    cancelled_sessions = Column(Integer, default=0, nullable=False)

    # Service metrics
    average_check_in_duration = Column(Integer, nullable=True)  # seconds
    average_retrieval_duration = Column(Integer, nullable=True)  # seconds
    average_total_duration = Column(Integer, nullable=True)  # seconds

    # Performance metrics
    peak_occupancy = Column(Integer, default=0, nullable=False)
    average_occupancy = Column(Numeric(5, 2), nullable=True)
    peak_wait_time = Column(Integer, nullable=True)  # minutes
    average_wait_time = Column(Integer, nullable=True)  # minutes

    # Financial metrics
    total_revenue = Column(Numeric(12, 2), default=0, nullable=False)
    total_tips = Column(Numeric(12, 2), default=0, nullable=False)
    average_tip_percentage = Column(Numeric(5, 2), nullable=True)

    # Service quality
    total_ratings = Column(Integer, default=0, nullable=False)
    average_rating = Column(Numeric(3, 2), nullable=True)

    # Incidents
    total_incidents = Column(Integer, default=0, nullable=False)
    incidents_by_type = Column(JSONB, nullable=True, default={})

    # Staffing
    average_attendants = Column(Numeric(5, 2), nullable=True)
    sessions_per_attendant = Column(Numeric(5, 2), nullable=True)

    # Additional metrics
    additional_metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue")

    # Indexes
    __table_args__ = (
        Index('ix_valet_metrics_daily_venue_date', 'venue_id', 'metric_date', unique=True),
        Index('ix_valet_metrics_daily_date', 'metric_date'),
    )

    def __repr__(self):
        return f"<ValetMetricsDaily venue={self.venue_id} date={self.metric_date.date()}>"


class KeyStorageConfig(Base):
    """Key storage configuration for venue valet service."""

    __tablename__ = "key_storage_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Storage layout configuration
    zones = Column(JSONB, nullable=False, default=list)
    # Example structure:
    # [
    #   {
    #     "id": "main",
    #     "name": "Main Storage",
    #     "type": "main",
    #     "boxes": [
    #       {
    #         "id": "box-1",
    #         "label": "Box 1",
    #         "positions": ["A1", "A2", "A3", ..., "A20"],
    #         "capacity": 20
    #       }
    #     ]
    #   }
    # ]

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue", foreign_keys=[venue_id])

    # Indexes
    __table_args__ = (
        Index('ix_key_storage_configs_venue', 'venue_id'),
    )

    def __repr__(self):
        return f"<KeyStorageConfig venue_id={self.venue_id}>"
