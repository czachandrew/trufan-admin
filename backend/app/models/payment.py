from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Payment(Base):
    """Payment model for tracking all financial transactions."""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(30), default=PaymentStatus.PENDING.value, nullable=False, index=True)

    # Payment method
    payment_method = Column(String(50), nullable=False)  # e.g., "card", "apple_pay", "google_pay"

    # Stripe integration
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True)

    # Polymorphic association to different payable types
    payable_type = Column(String(50), nullable=False)  # e.g., "order", "ticket", "parking_session"
    payable_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Refund tracking
    refunded_amount = Column(Numeric(10, 2), default=0, nullable=False)
    refund_reason = Column(String(500), nullable=True)

    # Metadata (using extra_data instead of reserved 'metadata')
    extra_data = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    succeeded_at = Column(DateTime, nullable=True)

    # Relationships
    splits = relationship("PaymentSplit", back_populates="payment", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_payments_payable', 'payable_type', 'payable_id'),
        Index('ix_payments_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f"<Payment {self.id} - {self.amount} {self.currency}>"


class PaymentSplit(Base):
    """Payment split model for revenue sharing (Stripe Connect)."""

    __tablename__ = "payment_splits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id", ondelete="SET NULL"), nullable=True, index=True)

    # Split details
    amount = Column(Numeric(10, 2), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=True)  # Optional: track percentage for reference

    # Recipient information
    recipient_type = Column(String(50), nullable=False)  # e.g., "platform", "venue", "merchant"
    stripe_account_id = Column(String(255), nullable=True)  # Stripe Connect account

    # Transfer tracking
    stripe_transfer_id = Column(String(255), nullable=True, unique=True)
    transfer_status = Column(String(30), default="pending", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="splits")

    def __repr__(self):
        return f"<PaymentSplit {self.id} - {self.amount}>"
