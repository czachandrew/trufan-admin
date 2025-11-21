from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Venue(Base):
    """Venue model for managing event locations."""

    __tablename__ = "venues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    # Contact information
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)

    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(50), default="USA", nullable=False)

    # Configuration (stored as JSONB for flexibility)
    configuration = Column(JSONB, nullable=True, default={})
    # Example config: {"timezone": "America/New_York", "currency": "USD", "features": {...}}

    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)

    # Stripe Connect account
    stripe_account_id = Column(String(255), nullable=True, unique=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    staff = relationship("VenueStaff", back_populates="venue", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="venue", cascade="all, delete-orphan")
    parking_lots = relationship("ParkingLot", back_populates="venue", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Venue {self.name}>"


class VenueStaff(Base):
    """Association table for venue staff members."""

    __tablename__ = "venue_staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)

    # Role at this venue
    role = Column(String(50), nullable=False)  # e.g., "admin", "manager", "staff"
    permissions = Column(JSONB, nullable=True, default={})

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="venue_staff")
    venue = relationship("Venue", back_populates="staff")

    # Indexes
    __table_args__ = (
        Index('ix_venue_staff_user_venue', 'user_id', 'venue_id', unique=True),
    )

    def __repr__(self):
        return f"<VenueStaff user_id={self.user_id} venue_id={self.venue_id}>"
