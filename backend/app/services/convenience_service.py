"""
Convenience Store Service Module

This module provides comprehensive business logic for managing the convenience store feature,
including item management, order processing, pricing calculations, and fulfillment operations.
"""

import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.convenience import (
    ConvenienceItem,
    ConvenienceOrder,
    ConvenienceOrderItem,
    ConvenienceOrderEvent,
    ConvenienceStoreConfig,
    ConvenienceOrderStatus,
    PaymentStatus,
    OrderItemStatus,
    ConvenienceItemCategory,
)
from app.models.venue import Venue
from app.models.user import User
from app.models.valet import ValetSession
from app.schemas.convenience import (
    ConvenienceItemCreate,
    ConvenienceItemUpdate,
    ConvenienceItemResponse,
    ConvenienceOrderCreate,
    ConvenienceOrderResponse,
    OrderItemResponse,
    OrderEventResponse,
    ConvenienceStoreConfigCreate,
    ConvenienceStoreConfigUpdate,
    ConvenienceStoreConfigResponse,
    PricingBreakdown,
)

logger = logging.getLogger(__name__)


class ConvenienceItemService:
    """Service for managing convenience store items."""

    @staticmethod
    def create_item(
        db: Session,
        item_data: ConvenienceItemCreate,
        created_by_id: Optional[UUID] = None
    ) -> ConvenienceItemResponse:
        """
        Create a new convenience item.

        Args:
            db: Database session
            item_data: Item creation data
            created_by_id: User creating the item

        Returns:
            Created item response

        Raises:
            HTTPException: If venue not found or validation fails
        """
        # Validate venue exists
        venue = db.query(Venue).filter(Venue.id == item_data.venue_id).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )

        # Calculate final price
        final_price = item_data.base_price + item_data.markup_amount
        if item_data.markup_percent > 0:
            final_price += (item_data.base_price * item_data.markup_percent / Decimal("100"))

        # Create item
        item = ConvenienceItem(
            id=uuid4(),
            venue_id=item_data.venue_id,
            name=item_data.name,
            description=item_data.description,
            image_url=item_data.image_url,
            category=item_data.category.value if item_data.category else None,
            base_price=item_data.base_price,
            markup_amount=item_data.markup_amount,
            markup_percent=item_data.markup_percent,
            final_price=final_price,
            source_store=item_data.source_store,
            source_address=item_data.source_address,
            estimated_shopping_time_minutes=item_data.estimated_shopping_time_minutes,
            requires_age_verification=item_data.requires_age_verification,
            max_quantity_per_order=item_data.max_quantity_per_order,
            tags=item_data.tags or [],
            sku=item_data.sku,
            barcode=item_data.barcode,
            created_by_id=created_by_id,
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        logger.info(f"Created convenience item {item.id} - {item.name}")

        return ConvenienceItemResponse.model_validate(item)

    @staticmethod
    def get_item(db: Session, item_id: UUID) -> ConvenienceItemResponse:
        """
        Get item by ID.

        Args:
            db: Database session
            item_id: Item ID

        Returns:
            Item response

        Raises:
            HTTPException: If item not found
        """
        item = db.query(ConvenienceItem).filter(ConvenienceItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        return ConvenienceItemResponse.model_validate(item)

    @staticmethod
    def list_items(
        db: Session,
        venue_id: UUID,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ConvenienceItemResponse], int]:
        """
        List items for a venue with filters.

        Args:
            db: Database session
            venue_id: Venue ID
            category: Filter by category
            is_active: Filter by active status
            search: Search in name/description
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (items list, total count)
        """
        query = db.query(ConvenienceItem).filter(ConvenienceItem.venue_id == venue_id)

        if category:
            query = query.filter(ConvenienceItem.category == category)

        if is_active is not None:
            query = query.filter(ConvenienceItem.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ConvenienceItem.name.ilike(search_pattern),
                    ConvenienceItem.description.ilike(search_pattern)
                )
            )

        total = query.count()

        offset = (page - 1) * page_size
        items = query.order_by(ConvenienceItem.name).offset(offset).limit(page_size).all()

        return ([ConvenienceItemResponse.model_validate(item) for item in items], total)

    @staticmethod
    def update_item(
        db: Session,
        item_id: UUID,
        item_data: ConvenienceItemUpdate
    ) -> ConvenienceItemResponse:
        """
        Update an existing item.

        Args:
            db: Database session
            item_id: Item ID
            item_data: Update data

        Returns:
            Updated item response

        Raises:
            HTTPException: If item not found
        """
        item = db.query(ConvenienceItem).filter(ConvenienceItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        # Update fields
        update_data = item_data.model_dump(exclude_unset=True)

        # Handle category enum
        if "category" in update_data and update_data["category"]:
            update_data["category"] = update_data["category"].value

        for field, value in update_data.items():
            if field != "category":  # Already handled
                setattr(item, field, value)

        # Recalculate final price if pricing fields changed
        if any(field in update_data for field in ["base_price", "markup_amount", "markup_percent"]):
            final_price = item.base_price + item.markup_amount
            if item.markup_percent > 0:
                final_price += (item.base_price * item.markup_percent / Decimal("100"))
            item.final_price = final_price

        item.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(item)

        logger.info(f"Updated convenience item {item.id}")

        return ConvenienceItemResponse.model_validate(item)

    @staticmethod
    def delete_item(db: Session, item_id: UUID) -> None:
        """
        Delete an item.

        Args:
            db: Database session
            item_id: Item ID

        Raises:
            HTTPException: If item not found
        """
        item = db.query(ConvenienceItem).filter(ConvenienceItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        db.delete(item)
        db.commit()

        logger.info(f"Deleted convenience item {item_id}")

    @staticmethod
    def toggle_item_active(db: Session, item_id: UUID) -> ConvenienceItemResponse:
        """
        Toggle item active status.

        Args:
            db: Database session
            item_id: Item ID

        Returns:
            Updated item response

        Raises:
            HTTPException: If item not found
        """
        item = db.query(ConvenienceItem).filter(ConvenienceItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )

        item.is_active = not item.is_active
        item.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(item)

        logger.info(f"Toggled item {item_id} active status to {item.is_active}")

        return ConvenienceItemResponse.model_validate(item)


class ConvenienceOrderService:
    """Service for managing convenience orders."""

    # Status transition rules
    VALID_TRANSITIONS: Dict[str, List[str]] = {
        ConvenienceOrderStatus.PENDING.value: [
            ConvenienceOrderStatus.CONFIRMED.value,
            ConvenienceOrderStatus.CANCELLED.value
        ],
        ConvenienceOrderStatus.CONFIRMED.value: [
            ConvenienceOrderStatus.SHOPPING.value,
            ConvenienceOrderStatus.CANCELLED.value
        ],
        ConvenienceOrderStatus.SHOPPING.value: [
            ConvenienceOrderStatus.PURCHASED.value,
            ConvenienceOrderStatus.CANCELLED.value
        ],
        ConvenienceOrderStatus.PURCHASED.value: [
            ConvenienceOrderStatus.STORED.value,
            ConvenienceOrderStatus.READY.value
        ],
        ConvenienceOrderStatus.STORED.value: [
            ConvenienceOrderStatus.READY.value
        ],
        ConvenienceOrderStatus.READY.value: [
            ConvenienceOrderStatus.DELIVERED.value
        ],
        ConvenienceOrderStatus.DELIVERED.value: [
            ConvenienceOrderStatus.COMPLETED.value
        ],
        ConvenienceOrderStatus.COMPLETED.value: [],
        ConvenienceOrderStatus.CANCELLED.value: [
            ConvenienceOrderStatus.REFUNDED.value
        ],
        ConvenienceOrderStatus.REFUNDED.value: [],
    }

    @staticmethod
    def generate_order_number(db: Session) -> str:
        """
        Generate unique order number in CS-XXXX format.

        Args:
            db: Database session

        Returns:
            Unique order number (e.g., "CS-1234")
        """
        max_attempts = 100
        for _ in range(max_attempts):
            number = secrets.randbelow(10000)
            order_number = f"CS-{number:04d}"

            exists = db.query(ConvenienceOrder).filter(
                ConvenienceOrder.order_number == order_number
            ).first()

            if not exists:
                return order_number

        # Fallback to UUID-based generation
        return f"CS-{uuid4().hex[:4].upper()}"

    @staticmethod
    def calculate_pricing(
        db: Session,
        venue_id: UUID,
        items: List[Tuple[ConvenienceItem, int]]
    ) -> PricingBreakdown:
        """
        Calculate pricing for an order.

        Args:
            db: Database session
            venue_id: Venue ID
            items: List of (item, quantity) tuples

        Returns:
            Pricing breakdown
        """
        # Get config
        config = db.query(ConvenienceStoreConfig).filter(
            ConvenienceStoreConfig.venue_id == venue_id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convenience store not configured for this venue"
            )

        # Calculate subtotal
        subtotal = Decimal("0")
        for item, quantity in items:
            subtotal += item.final_price * quantity

        # Calculate service fee
        service_fee = subtotal * (config.default_service_fee_percent / Decimal("100"))

        # Calculate tax (placeholder - would integrate with tax service)
        tax = Decimal("0")

        # Calculate total
        total = subtotal + service_fee + tax

        return PricingBreakdown(
            subtotal=subtotal,
            service_fee=service_fee,
            tax=tax,
            total=total
        )

    @staticmethod
    def create_order(
        db: Session,
        order_data: ConvenienceOrderCreate,
        user_id: UUID
    ) -> ConvenienceOrderResponse:
        """
        Create a new convenience order.

        Args:
            db: Database session
            order_data: Order creation data
            user_id: User placing the order

        Returns:
            Created order response

        Raises:
            HTTPException: If venue not found, items invalid, or validation fails
        """
        # Validate venue and config
        venue = db.query(Venue).filter(Venue.id == order_data.venue_id).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )

        config = db.query(ConvenienceStoreConfig).filter(
            ConvenienceStoreConfig.venue_id == order_data.venue_id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convenience store not configured for this venue"
            )

        if not config.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Convenience store is not enabled for this venue"
            )

        # Validate and fetch items
        items_with_quantities = []
        for order_item in order_data.items:
            item = db.query(ConvenienceItem).filter(
                and_(
                    ConvenienceItem.id == order_item.item_id,
                    ConvenienceItem.venue_id == order_data.venue_id,
                    ConvenienceItem.is_active == True
                )
            ).first()

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item {order_item.item_id} not found or not available"
                )

            if order_item.quantity > item.max_quantity_per_order:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity {order_item.quantity} exceeds maximum {item.max_quantity_per_order} for item {item.name}"
                )

            items_with_quantities.append((item, order_item.quantity))

        # Calculate pricing
        pricing = ConvenienceOrderService.calculate_pricing(
            db, order_data.venue_id, items_with_quantities
        )

        # Validate order amount
        if pricing.total < config.minimum_order_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order total ${pricing.total} is below minimum ${config.minimum_order_amount}"
            )

        if pricing.total > config.maximum_order_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order total ${pricing.total} exceeds maximum ${config.maximum_order_amount}"
            )

        # Generate order number
        order_number = ConvenienceOrderService.generate_order_number(db)

        # Calculate estimated ready time
        max_shopping_time = max(
            (item.estimated_shopping_time_minutes for item, _ in items_with_quantities),
            default=15
        )
        estimated_ready_time = datetime.utcnow() + timedelta(
            minutes=max_shopping_time + config.average_fulfillment_time_minutes
        )

        # Create order
        order = ConvenienceOrder(
            id=uuid4(),
            order_number=order_number,
            venue_id=order_data.venue_id,
            user_id=user_id,
            parking_session_id=order_data.parking_session_id,
            status=ConvenienceOrderStatus.PENDING.value,
            subtotal=pricing.subtotal,
            service_fee=pricing.service_fee,
            tax=pricing.tax,
            total_amount=pricing.total,
            delivery_instructions=order_data.delivery_instructions,
            special_instructions=order_data.special_instructions,
            estimated_ready_time=estimated_ready_time,
            complimentary_time_added_minutes=config.default_complimentary_parking_minutes,
        )

        db.add(order)
        db.flush()  # Get order ID

        # Create order items
        for item, quantity in items_with_quantities:
            line_total = item.final_price * quantity
            order_item = ConvenienceOrderItem(
                id=uuid4(),
                order_id=order.id,
                item_id=item.id,
                item_name=item.name,
                item_description=item.description,
                item_image_url=item.image_url,
                source_store=item.source_store,
                quantity=quantity,
                unit_price=item.final_price,
                line_total=line_total,
            )
            db.add(order_item)

        # Log initial event
        event = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.PENDING.value,
            notes="Order placed",
            created_by_id=user_id,
        )
        db.add(event)

        # Extend parking time if parking session provided
        if order_data.parking_session_id:
            parking_session = db.query(ValetSession).filter(
                ValetSession.id == order_data.parking_session_id
            ).first()
            if parking_session:
                # TODO: Implement parking time extension
                logger.info(f"Would extend parking session {parking_session.id} by {config.default_complimentary_parking_minutes} minutes")

        db.commit()
        db.refresh(order)

        logger.info(f"Created convenience order {order.id} - {order_number}")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def get_order(db: Session, order_id: UUID) -> ConvenienceOrderResponse:
        """
        Get order by ID with full details.

        Args:
            db: Database session
            order_id: Order ID

        Returns:
            Order response

        Raises:
            HTTPException: If order not found
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def list_user_orders(
        db: Session,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ConvenienceOrderResponse], int]:
        """
        List orders for a user.

        Args:
            db: Database session
            user_id: User ID
            status: Filter by status
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (orders list, total count)
        """
        query = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.user_id == user_id
        )

        if status:
            query = query.filter(ConvenienceOrder.status == status)

        total = query.count()

        offset = (page - 1) * page_size
        orders = query.order_by(desc(ConvenienceOrder.created_at)).offset(offset).limit(page_size).all()

        return ([ConvenienceOrderService._build_order_response(db, order) for order in orders], total)

    @staticmethod
    def list_venue_orders(
        db: Session,
        venue_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ConvenienceOrderResponse], int]:
        """
        List orders for a venue.

        Args:
            db: Database session
            venue_id: Venue ID
            status: Filter by status
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (orders list, total count)
        """
        query = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.venue_id == venue_id
        )

        if status:
            query = query.filter(ConvenienceOrder.status == status)

        total = query.count()

        offset = (page - 1) * page_size
        orders = query.order_by(desc(ConvenienceOrder.created_at)).offset(offset).limit(page_size).all()

        return ([ConvenienceOrderService._build_order_response(db, order) for order in orders], total)

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        cancellation_reason: str
    ) -> ConvenienceOrderResponse:
        """
        Cancel an order.

        Args:
            db: Database session
            order_id: Order ID
            user_id: User cancelling
            cancellation_reason: Reason for cancellation

        Returns:
            Updated order response

        Raises:
            HTTPException: If order not found or cannot be cancelled
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Can only cancel pending, confirmed, or shopping orders
        if order.status not in [
            ConvenienceOrderStatus.PENDING.value,
            ConvenienceOrderStatus.CONFIRMED.value,
            ConvenienceOrderStatus.SHOPPING.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status {order.status}"
            )

        old_status = order.status
        order.status = ConvenienceOrderStatus.CANCELLED.value
        order.cancelled_at = datetime.utcnow()
        order.cancellation_reason = cancellation_reason

        # Log event
        event = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.CANCELLED.value,
            notes=f"Order cancelled: {cancellation_reason}",
            created_by_id=user_id,
        )
        db.add(event)

        db.commit()
        db.refresh(order)

        logger.info(f"Cancelled order {order_id}: {cancellation_reason}")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def rate_order(
        db: Session,
        order_id: UUID,
        user_id: UUID,
        rating: int,
        feedback: Optional[str] = None,
        tip_amount: Optional[Decimal] = None
    ) -> ConvenienceOrderResponse:
        """
        Rate a completed order.

        Args:
            db: Database session
            order_id: Order ID
            user_id: User rating
            rating: Rating (1-5)
            feedback: Optional feedback
            tip_amount: Optional tip

        Returns:
            Updated order response

        Raises:
            HTTPException: If order not found or not completed
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status not in [
            ConvenienceOrderStatus.COMPLETED.value,
            ConvenienceOrderStatus.DELIVERED.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rate completed or delivered orders"
            )

        if rating < 1 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )

        order.rating = rating
        order.feedback = feedback

        if tip_amount and tip_amount > 0:
            order.tip_amount = tip_amount
            order.total_amount += tip_amount

        db.commit()
        db.refresh(order)

        logger.info(f"Order {order_id} rated: {rating} stars")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def _build_order_response(
        db: Session,
        order: ConvenienceOrder
    ) -> ConvenienceOrderResponse:
        """Build complete order response from model."""
        # Get venue name
        venue = db.query(Venue).filter(Venue.id == order.venue_id).first()
        venue_name = venue.name if venue else None

        # Get assigned staff name
        assigned_staff_name = None
        if order.assigned_staff_id:
            staff = db.query(User).filter(User.id == order.assigned_staff_id).first()
            if staff:
                assigned_staff_name = f"{staff.first_name} {staff.last_name}"

        # Get order items
        items = db.query(ConvenienceOrderItem).filter(
            ConvenienceOrderItem.order_id == order.id
        ).all()
        item_responses = [OrderItemResponse.model_validate(item) for item in items]

        # Get events
        events = db.query(ConvenienceOrderEvent).filter(
            ConvenienceOrderEvent.order_id == order.id
        ).order_by(ConvenienceOrderEvent.created_at).all()

        event_responses = []
        for event in events:
            created_by_name = None
            if event.created_by_id:
                user = db.query(User).filter(User.id == event.created_by_id).first()
                if user:
                    created_by_name = f"{user.first_name} {user.last_name}"

            event_responses.append(OrderEventResponse(
                id=event.id,
                order_id=event.order_id,
                status=event.status,
                notes=event.notes,
                photo_url=event.photo_url,
                location=event.location,
                created_by_id=event.created_by_id,
                created_by_name=created_by_name,
                created_at=event.created_at
            ))

        return ConvenienceOrderResponse(
            id=order.id,
            order_number=order.order_number,
            venue_id=order.venue_id,
            venue_name=venue_name,
            user_id=order.user_id,
            parking_session_id=order.parking_session_id,
            status=ConvenienceOrderStatus(order.status),
            subtotal=order.subtotal,
            service_fee=order.service_fee,
            tax=order.tax,
            tip_amount=order.tip_amount,
            total_amount=order.total_amount,
            payment_status=PaymentStatus(order.payment_status),
            payment_method=order.payment_method,
            assigned_staff_id=order.assigned_staff_id,
            assigned_staff_name=assigned_staff_name,
            storage_location=order.storage_location,
            delivery_instructions=order.delivery_instructions,
            special_instructions=order.special_instructions,
            receipt_photo_url=order.receipt_photo_url,
            delivery_photo_url=order.delivery_photo_url,
            estimated_ready_time=order.estimated_ready_time,
            confirmed_at=order.confirmed_at,
            shopping_started_at=order.shopping_started_at,
            purchased_at=order.purchased_at,
            stored_at=order.stored_at,
            ready_at=order.ready_at,
            delivered_at=order.delivered_at,
            completed_at=order.completed_at,
            cancelled_at=order.cancelled_at,
            complimentary_time_added_minutes=order.complimentary_time_added_minutes,
            rating=order.rating,
            feedback=order.feedback,
            cancellation_reason=order.cancellation_reason,
            refund_amount=order.refund_amount,
            refund_reason=order.refund_reason,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=item_responses,
            events=event_responses
        )


class ConvenienceStaffService:
    """Service for staff fulfillment operations."""

    @staticmethod
    def accept_order(
        db: Session,
        order_id: UUID,
        staff_id: UUID,
        estimated_ready_time: Optional[datetime] = None
    ) -> ConvenienceOrderResponse:
        """
        Accept an order for fulfillment.

        Args:
            db: Database session
            order_id: Order ID
            staff_id: Staff member accepting
            estimated_ready_time: Optional updated ETA

        Returns:
            Updated order response

        Raises:
            HTTPException: If order not found or wrong status
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status != ConvenienceOrderStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot accept order with status {order.status}"
            )

        order.status = ConvenienceOrderStatus.CONFIRMED.value
        order.assigned_staff_id = staff_id
        order.confirmed_at = datetime.utcnow()

        if estimated_ready_time:
            order.estimated_ready_time = estimated_ready_time

        # Log event
        event = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.CONFIRMED.value,
            notes="Order accepted by staff",
            created_by_id=staff_id,
        )
        db.add(event)

        db.commit()
        db.refresh(order)

        logger.info(f"Order {order_id} accepted by staff {staff_id}")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def start_shopping(
        db: Session,
        order_id: UUID,
        staff_id: UUID,
        notes: Optional[str] = None
    ) -> ConvenienceOrderResponse:
        """
        Mark order as shopping started.

        Args:
            db: Database session
            order_id: Order ID
            staff_id: Staff member shopping
            notes: Optional notes

        Returns:
            Updated order response
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status != ConvenienceOrderStatus.CONFIRMED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start shopping for order with status {order.status}"
            )

        order.status = ConvenienceOrderStatus.SHOPPING.value
        order.shopping_started_at = datetime.utcnow()

        # Log event
        event = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.SHOPPING.value,
            notes=notes or "Shopping started",
            created_by_id=staff_id,
        )
        db.add(event)

        db.commit()
        db.refresh(order)

        logger.info(f"Shopping started for order {order_id}")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def complete_shopping(
        db: Session,
        order_id: UUID,
        staff_id: UUID,
        receipt_photo_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ConvenienceOrderResponse:
        """
        Mark shopping as complete.

        Args:
            db: Database session
            order_id: Order ID
            staff_id: Staff member
            receipt_photo_url: Optional receipt photo
            notes: Optional notes

        Returns:
            Updated order response
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status != ConvenienceOrderStatus.SHOPPING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete shopping for order with status {order.status}"
            )

        order.status = ConvenienceOrderStatus.PURCHASED.value
        order.purchased_at = datetime.utcnow()

        if receipt_photo_url:
            order.receipt_photo_url = receipt_photo_url

        # Log event
        event = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.PURCHASED.value,
            notes=notes or "Shopping completed, items purchased",
            photo_url=receipt_photo_url,
            created_by_id=staff_id,
        )
        db.add(event)

        db.commit()
        db.refresh(order)

        logger.info(f"Shopping completed for order {order_id}")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def store_order(
        db: Session,
        order_id: UUID,
        staff_id: UUID,
        storage_location: str,
        notes: Optional[str] = None
    ) -> ConvenienceOrderResponse:
        """
        Store items at location.

        Args:
            db: Database session
            order_id: Order ID
            staff_id: Staff member
            storage_location: Storage location
            notes: Optional notes

        Returns:
            Updated order response
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status != ConvenienceOrderStatus.PURCHASED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot store order with status {order.status}"
            )

        order.status = ConvenienceOrderStatus.STORED.value
        order.stored_at = datetime.utcnow()
        order.storage_location = storage_location

        # Also mark as ready
        order.status = ConvenienceOrderStatus.READY.value
        order.ready_at = datetime.utcnow()

        # Log events
        event1 = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.STORED.value,
            notes=notes or f"Items stored at {storage_location}",
            location=storage_location,
            created_by_id=staff_id,
        )
        db.add(event1)

        event2 = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.READY.value,
            notes="Order ready for pickup/delivery",
            location=storage_location,
            created_by_id=staff_id,
        )
        db.add(event2)

        db.commit()
        db.refresh(order)

        logger.info(f"Order {order_id} stored at {storage_location}")

        return ConvenienceOrderService._build_order_response(db, order)

    @staticmethod
    def deliver_order(
        db: Session,
        order_id: UUID,
        staff_id: UUID,
        delivery_photo_url: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ConvenienceOrderResponse:
        """
        Mark order as delivered.

        Args:
            db: Database session
            order_id: Order ID
            staff_id: Staff member
            delivery_photo_url: Optional delivery photo
            notes: Optional notes

        Returns:
            Updated order response
        """
        order = db.query(ConvenienceOrder).filter(
            ConvenienceOrder.id == order_id
        ).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.status != ConvenienceOrderStatus.READY.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deliver order with status {order.status}"
            )

        order.status = ConvenienceOrderStatus.DELIVERED.value
        order.delivered_at = datetime.utcnow()

        if delivery_photo_url:
            order.delivery_photo_url = delivery_photo_url

        # Auto-complete
        order.status = ConvenienceOrderStatus.COMPLETED.value
        order.completed_at = datetime.utcnow()

        # Log events
        event1 = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.DELIVERED.value,
            notes=notes or "Order delivered to customer",
            photo_url=delivery_photo_url,
            created_by_id=staff_id,
        )
        db.add(event1)

        event2 = ConvenienceOrderEvent(
            id=uuid4(),
            order_id=order.id,
            status=ConvenienceOrderStatus.COMPLETED.value,
            notes="Order completed",
            created_by_id=staff_id,
        )
        db.add(event2)

        db.commit()
        db.refresh(order)

        logger.info(f"Order {order_id} delivered and completed")

        return ConvenienceOrderService._build_order_response(db, order)


class ConvenienceConfigService:
    """Service for managing convenience store configuration."""

    @staticmethod
    def get_or_create_config(
        db: Session,
        venue_id: UUID
    ) -> ConvenienceStoreConfigResponse:
        """
        Get config or create with defaults if not exists.

        Args:
            db: Database session
            venue_id: Venue ID

        Returns:
            Config response
        """
        config = db.query(ConvenienceStoreConfig).filter(
            ConvenienceStoreConfig.venue_id == venue_id
        ).first()

        if not config:
            # Create default config
            config = ConvenienceStoreConfig(
                id=uuid4(),
                venue_id=venue_id,
                storage_locations=["Vehicle Trunk", "Front Desk", "Refrigerator", "Locker"]
            )
            db.add(config)
            db.commit()
            db.refresh(config)

        return ConvenienceStoreConfigResponse.model_validate(config)

    @staticmethod
    def update_config(
        db: Session,
        venue_id: UUID,
        config_data: ConvenienceStoreConfigUpdate
    ) -> ConvenienceStoreConfigResponse:
        """
        Update convenience store configuration.

        Args:
            db: Database session
            venue_id: Venue ID
            config_data: Update data

        Returns:
            Updated config response
        """
        config = db.query(ConvenienceStoreConfig).filter(
            ConvenienceStoreConfig.venue_id == venue_id
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration not found"
            )

        # Update fields
        update_data = config_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(config)

        logger.info(f"Updated convenience store config for venue {venue_id}")

        return ConvenienceStoreConfigResponse.model_validate(config)
