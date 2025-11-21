from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class EventStatus(str, enum.Enum):
    """Event status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(Base):
    """Event model for ticketing and management."""

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Event timing
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    doors_open = Column(DateTime, nullable=True)

    # Capacity and pricing
    total_capacity = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)

    # Status
    status = Column(String(20), default=EventStatus.DRAFT.value, nullable=False, index=True)

    # Configuration
    configuration = Column(JSONB, nullable=True, default={})
    # Example: {"ticket_types": [...], "seating": {...}, "age_restriction": 21}

    # Media
    image_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue", back_populates="events")
    tickets = relationship("Ticket", back_populates="event", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_events_venue_start_time', 'venue_id', 'start_time'),
        Index('ix_events_status_start_time', 'status', 'start_time'),
    )

    def __repr__(self):
        return f"<Event {self.name}>"
