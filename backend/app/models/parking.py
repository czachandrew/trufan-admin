from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ParkingStatus(str, enum.Enum):
    """Parking session status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ParkingSpace(Base):
    """Individual parking space within a lot."""

    __tablename__ = "parking_spaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("parking_lots.id", ondelete="CASCADE"), nullable=False, index=True)

    # Space information
    space_number = Column(String(20), nullable=False)
    space_type = Column(String(50), default="standard", nullable=False)  # standard, handicap, ev, valet

    # Status
    is_occupied = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    lot = relationship("ParkingLot", back_populates="spaces")

    __table_args__ = (
        Index('ix_parking_spaces_lot_number', 'lot_id', 'space_number', unique=True),
    )

    def __repr__(self):
        return f"<ParkingSpace {self.space_number}>"


class ParkingLot(Base):
    """Parking lot model for venue parking management."""

    __tablename__ = "parking_lots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Lot information
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    location_address = Column(String(500), nullable=True)
    total_spaces = Column(Integer, nullable=False)
    available_spaces = Column(Integer, nullable=False)

    # Location
    location_lat = Column(Numeric(10, 8), nullable=True)
    location_lng = Column(Numeric(11, 8), nullable=True)

    # Pricing configuration (dynamic pricing support)
    pricing_config = Column(JSONB, nullable=True, default={})
    # Example: {"base_rate": 10.00, "hourly_rate": 5.00, "max_daily": 50.00, "dynamic_multiplier": 1.0}

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue", back_populates="parking_lots")
    owner = relationship("User", foreign_keys=[owner_id])
    spaces = relationship("ParkingSpace", back_populates="lot", cascade="all, delete-orphan")
    sessions = relationship("ParkingSession", back_populates="parking_lot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ParkingLot {self.name}>"


class ParkingSession(Base):
    """Parking session model for tracking parking usage."""

    __tablename__ = "parking_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("parking_lots.id", ondelete="CASCADE"), nullable=False, index=True)
    space_id = Column(UUID(as_uuid=True), ForeignKey("parking_spaces.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Vehicle information
    vehicle_plate = Column(String(20), nullable=False, index=True)
    vehicle_make = Column(String(50), nullable=True)
    vehicle_model = Column(String(50), nullable=True)
    vehicle_color = Column(String(30), nullable=True)

    # Session timing
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    # Pricing
    base_price = Column(Numeric(10, 2), nullable=False)
    actual_price = Column(Numeric(10, 2), nullable=True)
    dynamic_multiplier = Column(Numeric(4, 2), default=1.0, nullable=False)

    # Public access (no auth required)
    access_code = Column(String(20), nullable=False, unique=True, index=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)

    # Notifications
    last_notification_sent = Column(DateTime, nullable=True)

    # Status
    status = Column(String(20), default=ParkingStatus.ACTIVE.value, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    parking_lot = relationship("ParkingLot", back_populates="sessions")
    space = relationship("ParkingSpace")
    user = relationship("User", back_populates="parking_sessions")

    # Indexes
    __table_args__ = (
        Index('ix_parking_sessions_lot_status', 'lot_id', 'status'),
        Index('ix_parking_sessions_user_status', 'user_id', 'status'),
        Index('ix_parking_sessions_expires_at', 'expires_at'),
        Index('ix_parking_sessions_access_code', 'access_code'),
    )

    def __repr__(self):
        return f"<ParkingSession {self.id} - {self.vehicle_plate}>"
