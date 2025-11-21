from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderableType(str, enum.Enum):
    """Type of orderable item."""
    CONCESSION = "concession"
    MERCHANDISE = "merchandise"
    TICKET = "ticket"


class Order(Base):
    """Order model for concessions and merchandise."""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="SET NULL"), nullable=True, index=True)

    # Order details
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    tip_amount = Column(Numeric(10, 2), default=0, nullable=True)

    # Status
    status = Column(String(20), default=OrderStatus.PENDING.value, nullable=False, index=True)

    # Delivery information
    delivery_method = Column(String(50), nullable=True)  # e.g., "pickup", "seat_delivery", "shipping"
    delivery_location = Column(String(255), nullable=True)  # e.g., "Section A, Row 5, Seat 12"
    delivery_notes = Column(String(500), nullable=True)

    # Additional metadata (using extra_data instead of reserved 'metadata')
    extra_data = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_orders_user_status', 'user_id', 'status'),
        Index('ix_orders_venue_status', 'venue_id', 'status'),
    )

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(Base):
    """Order item model for individual items in an order."""

    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item details
    orderable_type = Column(String(50), nullable=False)  # concession, merchandise, ticket
    orderable_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the actual item

    # Product information (denormalized for historical record)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)

    # Customization
    customization = Column(JSONB, nullable=True, default={})
    # Example: {"size": "large", "extras": ["cheese", "bacon"]}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem {self.name} x{self.quantity}>"
