"""
Staff API Endpoints for Convenience Store

This module provides staff-facing endpoints for fulfilling convenience orders,
including accepting orders, shopping, storing, and delivering items.

All endpoints require venue_staff, venue_admin, or super_admin role.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.venue import VenueStaff
from app.models.convenience import ConvenienceOrder, ConvenienceOrderStatus, OrderItemStatus
from app.schemas.convenience import (
    ConvenienceOrderResponse,
    ConvenienceOrderList,
    ConvenienceOrderSummary,
    OrderAcceptRequest,
    OrderStartShoppingRequest,
    OrderCompleteShoppingRequest,
    OrderStoreRequest,
    OrderDeliverRequest,
    OrderItemUpdateStatus,
)
from app.services.convenience_service import (
    ConvenienceOrderService,
    ConvenienceStaffService,
)

router = APIRouter(tags=["convenience-staff"])


def check_staff_permissions(current_user: User, venue_id: Optional[UUID] = None, db: Session = None) -> None:
    """
    Verify user has staff permissions for convenience operations.

    Args:
        current_user: Current authenticated user
        venue_id: Optional venue ID for venue-specific checks
        db: Database session for venue staff lookup

    Raises:
        HTTPException: If user lacks required permissions
    """
    # Check if user has staff or admin role
    if current_user.role not in [UserRole.VENUE_STAFF, UserRole.VENUE_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or admin role required for this operation"
        )

    # Super admins have access to all venues
    if current_user.role == UserRole.SUPER_ADMIN:
        return

    # For venue_staff and venue_admin, check venue association
    if venue_id and db:
        venue_staff_record = db.query(VenueStaff).filter(
            and_(
                VenueStaff.user_id == current_user.id,
                VenueStaff.venue_id == venue_id,
                VenueStaff.is_active == True
            )
        ).first()

        if not venue_staff_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this venue"
            )


# Order Queue Endpoints

@router.get("/venues/{venue_id}/orders", response_model=ConvenienceOrderList)
def get_venue_order_queue(
    venue_id: UUID,
    status: Optional[str] = Query(None, description="Filter by order status"),
    assigned_to_me: bool = Query(False, description="Show only orders assigned to me"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Orders per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get order queue for staff fulfillment dashboard.

    Returns orders that need attention, optionally filtered by:
    - Status (pending, confirmed, shopping, etc.)
    - Assignment (only orders assigned to current staff member)

    Useful for displaying active orders needing fulfillment.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, venue_id, db)

    # Build query
    query = db.query(ConvenienceOrder).filter(
        ConvenienceOrder.venue_id == venue_id
    )

    if status:
        query = query.filter(ConvenienceOrder.status == status)

    if assigned_to_me:
        query = query.filter(ConvenienceOrder.assigned_staff_id == current_user.id)

    # Get orders
    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(ConvenienceOrder.created_at).offset(offset).limit(page_size).all()

    # Convert to response format
    order_responses = [ConvenienceOrderService._build_order_response(db, order) for order in orders]

    # Convert to summary format
    summaries = []
    for order in order_responses:
        summaries.append(ConvenienceOrderSummary(
            id=order.id,
            order_number=order.order_number,
            venue_name=order.venue_name,
            status=order.status,
            total_amount=order.total_amount,
            item_count=len(order.items),
            estimated_ready_time=order.estimated_ready_time,
            created_at=order.created_at
        ))

    return ConvenienceOrderList(
        orders=summaries,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/orders/{order_id}", response_model=ConvenienceOrderResponse)
def get_order_for_staff(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed order information for fulfillment.

    Returns complete order details including items, customer instructions,
    timeline, and current status.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)

    # Check venue access
    check_staff_permissions(current_user, order.venue_id, db)

    return order


# Order Fulfillment Workflow Endpoints

@router.patch("/orders/{order_id}/accept", response_model=ConvenienceOrderResponse)
def accept_order(
    order_id: UUID,
    accept_data: OrderAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accept an order for fulfillment.

    Staff member accepts responsibility for shopping and fulfilling the order.
    Moves order from 'pending' to 'confirmed' status.

    Optional: Update the estimated ready time if it needs adjustment.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get order to check venue
    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    return ConvenienceStaffService.accept_order(
        db=db,
        order_id=order_id,
        staff_id=current_user.id,
        estimated_ready_time=accept_data.estimated_ready_time
    )


@router.patch("/orders/{order_id}/start-shopping", response_model=ConvenienceOrderResponse)
def start_shopping(
    order_id: UUID,
    shopping_data: OrderStartShoppingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark order as shopping started.

    Staff member begins shopping for the items at the source store.
    Moves order from 'confirmed' to 'shopping' status.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    return ConvenienceStaffService.start_shopping(
        db=db,
        order_id=order_id,
        staff_id=current_user.id,
        notes=shopping_data.notes
    )


@router.patch("/orders/{order_id}/complete-shopping", response_model=ConvenienceOrderResponse)
def complete_shopping(
    order_id: UUID,
    completion_data: OrderCompleteShoppingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark shopping as complete.

    Staff member has finished shopping and purchased all items.
    Moves order from 'shopping' to 'purchased' status.

    Optional: Upload receipt photo for proof of purchase.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    return ConvenienceStaffService.complete_shopping(
        db=db,
        order_id=order_id,
        staff_id=current_user.id,
        receipt_photo_url=completion_data.receipt_photo_url,
        notes=completion_data.notes
    )


@router.patch("/orders/{order_id}/store", response_model=ConvenienceOrderResponse)
def store_items(
    order_id: UUID,
    storage_data: OrderStoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Store items at designated location.

    Staff member stores the purchased items at the specified location
    (e.g., customer's trunk, locker, refrigerator).

    This also marks the order as 'ready' for customer pickup/notification.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    return ConvenienceStaffService.store_order(
        db=db,
        order_id=order_id,
        staff_id=current_user.id,
        storage_location=storage_data.storage_location,
        notes=storage_data.notes
    )


@router.patch("/orders/{order_id}/deliver", response_model=ConvenienceOrderResponse)
def deliver_order(
    order_id: UUID,
    delivery_data: OrderDeliverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark order as delivered.

    Staff member delivers the items to the customer and confirms delivery.
    This automatically completes the order.

    Optional: Upload delivery photo for proof of delivery.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    return ConvenienceStaffService.deliver_order(
        db=db,
        order_id=order_id,
        staff_id=current_user.id,
        delivery_photo_url=delivery_data.delivery_photo_url,
        notes=delivery_data.notes
    )


# Order Item Management

@router.post("/orders/{order_id}/items/{item_id}/update", response_model=ConvenienceOrderResponse)
def update_order_item_status(
    order_id: UUID,
    item_id: UUID,
    item_update: OrderItemUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update individual order item status.

    Allows staff to mark items as:
    - found: Item found and will be purchased
    - not_found: Item not available at store
    - substituted: Item substituted with alternative

    Useful for managing item availability during shopping.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    # Get the order item
    from app.models.convenience import ConvenienceOrderItem
    from datetime import datetime

    order_item = db.query(ConvenienceOrderItem).filter(
        ConvenienceOrderItem.id == item_id,
        ConvenienceOrderItem.order_id == order_id
    ).first()

    if not order_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )

    # Update item status
    order_item.status = item_update.status.value
    if item_update.substitution_notes:
        order_item.substitution_notes = item_update.substitution_notes
    if item_update.actual_price:
        order_item.actual_price = item_update.actual_price

    # Log event
    from app.models.convenience import ConvenienceOrderEvent
    from uuid import uuid4

    event = ConvenienceOrderEvent(
        id=uuid4(),
        order_id=order_id,
        status=f"item_update_{item_update.status.value}",
        notes=f"Item '{order_item.item_name}' marked as {item_update.status.value}" +
              (f": {item_update.substitution_notes}" if item_update.substitution_notes else ""),
        created_by_id=current_user.id,
    )
    db.add(event)

    db.commit()

    return ConvenienceOrderService.get_order(db=db, order_id=order_id)


@router.post("/orders/{order_id}/upload-receipt", response_model=ConvenienceOrderResponse)
def upload_receipt(
    order_id: UUID,
    receipt_url: str = Query(..., description="URL to uploaded receipt photo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload receipt photo for an order.

    Allows staff to add or update the receipt photo after shopping.
    Useful if the photo wasn't uploaded during the complete-shopping step.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)
    check_staff_permissions(current_user, order.venue_id, db)

    # Update receipt URL
    db_order = db.query(ConvenienceOrder).filter(
        ConvenienceOrder.id == order_id
    ).first()

    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    db_order.receipt_photo_url = receipt_url

    # Log event
    from app.models.convenience import ConvenienceOrderEvent
    from uuid import uuid4
    from datetime import datetime

    event = ConvenienceOrderEvent(
        id=uuid4(),
        order_id=order_id,
        status=db_order.status,
        notes="Receipt photo uploaded",
        photo_url=receipt_url,
        created_by_id=current_user.id,
    )
    db.add(event)

    db.commit()

    return ConvenienceOrderService.get_order(db=db, order_id=order_id)
