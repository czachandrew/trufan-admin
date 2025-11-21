from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    USED = "used"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Ticket(Base):
    """Ticket model for event access."""

    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ticket details
    ticket_type = Column(String(50), nullable=False)  # e.g., "general", "vip", "early_bird"
    price = Column(Numeric(10, 2), nullable=False)
    qr_code = Column(String(255), unique=True, nullable=False, index=True)

    # Status and validation
    status = Column(String(20), default=TicketStatus.PENDING.value, nullable=False, index=True)
    validated_at = Column(DateTime, nullable=True)
    validated_by = Column(UUID(as_uuid=True), nullable=True)  # Staff user who validated

    # Seat assignment (if applicable)
    seat_section = Column(String(50), nullable=True)
    seat_row = Column(String(10), nullable=True)
    seat_number = Column(String(10), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="tickets")
    user = relationship("User", back_populates="tickets")

    # Indexes
    __table_args__ = (
        Index('ix_tickets_event_status', 'event_id', 'status'),
        Index('ix_tickets_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f"<Ticket {self.id} for event {self.event_id}>"
