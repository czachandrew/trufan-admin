"""
Convenience Store Models

This module defines database models for the on-premise convenience store feature,
allowing parking lot owners to offer shopping and delivery services to parkers.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Boolean, Index, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ConvenienceItemCategory(str, enum.Enum):
    """Product category for convenience items."""
    GROCERY = "grocery"
    FOOD = "food"
    BEVERAGE = "beverage"
    PERSONAL_CARE = "personal_care"
    ELECTRONICS = "electronics"
    OTHER = "other"


class ConvenienceOrderStatus(str, enum.Enum):
    """Order status for convenience orders."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHOPPING = "shopping"
    PURCHASED = "purchased"
    STORED = "stored"
    READY = "ready"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    """Payment status for orders."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class OrderItemStatus(str, enum.Enum):
    """Status for individual order items."""
    PENDING = "pending"
    FOUND = "found"
    NOT_FOUND = "not_found"
    SUBSTITUTED = "substituted"
    DELIVERED = "delivered"


class ConvenienceItem(Base):
    """Items available for purchase at a venue."""

    __tablename__ = "convenience_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)

    # Pricing
    base_price = Column(Numeric(10, 2), nullable=False)  # Cost at store
    markup_amount = Column(Numeric(10, 2), default=0, nullable=False)  # Fixed markup
    markup_percent = Column(Numeric(5, 2), default=0, nullable=False)  # Percentage markup
    final_price = Column(Numeric(10, 2), nullable=False)  # What customer pays

    # Source
    source_store = Column(String(200), nullable=False)  # 'Walgreens', 'CVS', etc.
    source_address = Column(Text, nullable=True)
    estimated_shopping_time_minutes = Column(Integer, default=15, nullable=False)

    # Availability
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    requires_age_verification = Column(Boolean, default=False, nullable=False)
    max_quantity_per_order = Column(Integer, default=10, nullable=False)

    # Metadata
    tags = Column(ARRAY(String), nullable=True, default=list)
    sku = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True)

    # Time tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    venue = relationship("Venue", foreign_keys=[venue_id])
    created_by = relationship("User", foreign_keys=[created_by_id])

    # Indexes
    __table_args__ = (
        Index('ix_convenience_items_venue_active', 'venue_id', 'is_active'),
        Index('ix_convenience_items_category', 'category'),
        Index('ix_convenience_items_source_store', 'source_store'),
    )

    def __repr__(self):
        return f"<ConvenienceItem {self.name} - ${self.final_price}>"


class ConvenienceOrder(Base):
    """Orders placed by parkers."""

    __tablename__ = "convenience_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)

    # Relationships
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parking_session_id = Column(UUID(as_uuid=True), ForeignKey("valet_sessions.id", ondelete="SET NULL"), nullable=True)

    # Order details
    status = Column(String(30), default=ConvenienceOrderStatus.PENDING.value, nullable=False, index=True)

    # Pricing
    subtotal = Column(Numeric(10, 2), nullable=False)  # Sum of item prices
    service_fee = Column(Numeric(10, 2), nullable=False)  # Lot's fee for service
    tax = Column(Numeric(10, 2), default=0, nullable=False)
    tip_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Payment
    payment_status = Column(String(30), default=PaymentStatus.PENDING.value, nullable=False)
    payment_intent_id = Column(String(200), nullable=True)  # Stripe payment intent
    payment_method = Column(String(50), nullable=True)  # card, apple_pay, google_pay

    # Fulfillment
    assigned_staff_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    storage_location = Column(String(100), nullable=True)  # 'Trunk', 'Locker 5', etc.
    delivery_instructions = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)

    # Proof
    receipt_photo_url = Column(Text, nullable=True)
    delivery_photo_url = Column(Text, nullable=True)

    # Timing
    estimated_ready_time = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    shopping_started_at = Column(DateTime, nullable=True)
    purchased_at = Column(DateTime, nullable=True)
    stored_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Parking integration
    complimentary_time_added_minutes = Column(Integer, default=0, nullable=False)

    # Rating
    rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)

    # Metadata
    cancellation_reason = Column(Text, nullable=True)
    refund_amount = Column(Numeric(10, 2), nullable=True)
    refund_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue", foreign_keys=[venue_id])
    user = relationship("User", foreign_keys=[user_id])
    parking_session = relationship("ValetSession", foreign_keys=[parking_session_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    items = relationship("ConvenienceOrderItem", back_populates="order", cascade="all, delete-orphan")
    events = relationship("ConvenienceOrderEvent", back_populates="order", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        Index('ix_convenience_orders_venue_status', 'venue_id', 'status'),
        Index('ix_convenience_orders_user', 'user_id'),
        Index('ix_convenience_orders_parking_session', 'parking_session_id'),
        Index('ix_convenience_orders_order_number', 'order_number'),
        Index('ix_convenience_orders_status', 'status'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    def __repr__(self):
        return f"<ConvenienceOrder {self.order_number} - {self.status}>"


class ConvenienceOrderItem(Base):
    """Line items in an order."""

    __tablename__ = "convenience_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("convenience_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("convenience_items.id", ondelete="SET NULL"), nullable=True)

    # Snapshot of item at time of order (in case item changes/deleted)
    item_name = Column(String(200), nullable=False)
    item_description = Column(Text, nullable=True)
    item_image_url = Column(Text, nullable=True)
    source_store = Column(String(200), nullable=True)

    # Pricing at time of order
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)  # quantity * unit_price

    # Fulfillment
    status = Column(String(30), default=OrderItemStatus.PENDING.value, nullable=False)
    substitution_notes = Column(Text, nullable=True)
    actual_price = Column(Numeric(10, 2), nullable=True)  # Actual price paid at store

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("ConvenienceOrder", back_populates="items")
    item = relationship("ConvenienceItem", foreign_keys=[item_id])

    # Indexes
    __table_args__ = (
        Index('ix_convenience_order_items_order', 'order_id'),
    )

    def __repr__(self):
        return f"<ConvenienceOrderItem {self.item_name} x{self.quantity}>"


class ConvenienceOrderEvent(Base):
    """Status change history for orders."""

    __tablename__ = "convenience_order_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("convenience_orders.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    photo_url = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    order = relationship("ConvenienceOrder", back_populates="events")
    created_by = relationship("User", foreign_keys=[created_by_id])

    # Indexes
    __table_args__ = (
        Index('ix_convenience_order_events_order_created', 'order_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ConvenienceOrderEvent {self.order_id} - {self.status}>"


class ConvenienceStoreConfig(Base):
    """Configuration for convenience store feature per venue."""

    __tablename__ = "convenience_store_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Feature toggle
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Pricing
    default_service_fee_percent = Column(Numeric(5, 2), default=15.00, nullable=False)
    minimum_order_amount = Column(Numeric(10, 2), default=5.00, nullable=False)
    maximum_order_amount = Column(Numeric(10, 2), default=200.00, nullable=False)

    # Timing
    default_complimentary_parking_minutes = Column(Integer, default=15, nullable=False)
    average_fulfillment_time_minutes = Column(Integer, default=30, nullable=False)

    # Availability
    operating_hours = Column(JSONB, nullable=True)  # {"monday": {"open": "08:00", "close": "20:00"}, ...}

    # Messaging
    welcome_message = Column(Text, default='Want us to grab a few things for you while you park?', nullable=True)
    instructions_message = Column(Text, nullable=True)

    # Storage locations available
    storage_locations = Column(ARRAY(String), default=list, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    venue = relationship("Venue", foreign_keys=[venue_id])

    # Indexes
    __table_args__ = (
        Index('ix_convenience_store_config_venue', 'venue_id'),
    )

    def __repr__(self):
        return f"<ConvenienceStoreConfig venue={self.venue_id} enabled={self.is_enabled}>"
