"""
Admin API Endpoints for Convenience Store

This module provides lot owner/admin endpoints for managing convenience store items,
configuration, and viewing orders.

All endpoints require venue_admin or super_admin role.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.venue import Venue, VenueStaff
from app.schemas.convenience import (
    ConvenienceItemCreate,
    ConvenienceItemUpdate,
    ConvenienceItemResponse,
    ConvenienceItemList,
    ConvenienceOrderResponse,
    ConvenienceOrderList,
    ConvenienceOrderSummary,
    ConvenienceStoreConfigResponse,
    ConvenienceStoreConfigUpdate,
    ItemBulkImportRequest,
    ItemBulkImportResponse,
    CategoriesResponse,
    OrderRefundRequest,
    ConvenienceItemCategory,
)
from app.services.convenience_service import (
    ConvenienceItemService,
    ConvenienceOrderService,
    ConvenienceConfigService,
)

router = APIRouter(tags=["convenience-admin"])


def check_admin_permissions(current_user: User, venue_id: UUID, db: Session) -> None:
    """
    Verify user has admin permissions for venue.

    Args:
        current_user: Current authenticated user
        venue_id: Venue ID
        db: Database session

    Raises:
        HTTPException: If user lacks required permissions
    """
    # Super admins have access to all venues
    if current_user.role == UserRole.SUPER_ADMIN:
        return

    # Check if user is venue admin
    if current_user.role == UserRole.VENUE_ADMIN:
        # Verify user is associated with this venue
        venue_staff = db.query(VenueStaff).filter(
            VenueStaff.user_id == current_user.id,
            VenueStaff.venue_id == venue_id,
            VenueStaff.is_active == True
        ).first()

        if not venue_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have admin access to this venue"
            )
        return

    # All other roles are not allowed
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin role required for this operation"
    )


# Item Management Endpoints

@router.get("/venues/{venue_id}/items", response_model=ConvenienceItemList)
def list_venue_items(
    venue_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all convenience items for a venue.

    Supports filtering by category, active status, and text search.
    Returns paginated results.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    items, total = ConvenienceItemService.list_items(
        db=db,
        venue_id=venue_id,
        category=category,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size
    )

    return ConvenienceItemList(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/venues/{venue_id}/items", response_model=ConvenienceItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    venue_id: UUID,
    item_data: ConvenienceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new convenience item.

    The final_price is automatically calculated based on base_price, markup_amount, and markup_percent.
    Formula: final_price = base_price + markup_amount + (base_price * markup_percent / 100)

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    # Ensure venue_id matches
    if item_data.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue ID in path must match venue ID in request body"
        )

    return ConvenienceItemService.create_item(
        db=db,
        item_data=item_data,
        created_by_id=current_user.id
    )


@router.get("/venues/{venue_id}/items/{item_id}", response_model=ConvenienceItemResponse)
def get_item(
    venue_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific convenience item by ID.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    item = ConvenienceItemService.get_item(db=db, item_id=item_id)

    # Verify item belongs to venue
    if item.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item


@router.put("/venues/{venue_id}/items/{item_id}", response_model=ConvenienceItemResponse)
def update_item(
    venue_id: UUID,
    item_id: UUID,
    item_data: ConvenienceItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing convenience item.

    Only provided fields will be updated. The final_price is recalculated
    if any pricing fields (base_price, markup_amount, markup_percent) are changed.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    # Verify item belongs to venue
    item = ConvenienceItemService.get_item(db=db, item_id=item_id)
    if item.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return ConvenienceItemService.update_item(
        db=db,
        item_id=item_id,
        item_data=item_data
    )


@router.delete("/venues/{venue_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    venue_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a convenience item.

    This permanently deletes the item. Items referenced in existing orders
    will still appear in those orders (via snapshot data).

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    # Verify item belongs to venue
    item = ConvenienceItemService.get_item(db=db, item_id=item_id)
    if item.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    ConvenienceItemService.delete_item(db=db, item_id=item_id)


@router.patch("/venues/{venue_id}/items/{item_id}/toggle", response_model=ConvenienceItemResponse)
def toggle_item_active(
    venue_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle item active/inactive status.

    Inactive items are not visible to customers but are preserved in the system.
    This is useful for seasonal items or temporary unavailability.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    # Verify item belongs to venue
    item = ConvenienceItemService.get_item(db=db, item_id=item_id)
    if item.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return ConvenienceItemService.toggle_item_active(db=db, item_id=item_id)


@router.post("/venues/{venue_id}/items/bulk-import", response_model=ItemBulkImportResponse)
def bulk_import_items(
    venue_id: UUID,
    import_data: ItemBulkImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk import multiple convenience items.

    This endpoint allows importing multiple items at once. Each item is validated
    individually, and the response includes both successfully imported items and
    any errors encountered.

    Partial success is allowed - some items may succeed while others fail.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    success_count = 0
    error_count = 0
    errors = []
    imported_items = []

    for idx, item_row in enumerate(import_data.items):
        try:
            # Create item data
            item_create = ConvenienceItemCreate(
                venue_id=venue_id,
                name=item_row.name,
                description=item_row.description,
                category=ConvenienceItemCategory(item_row.category) if item_row.category else None,
                base_price=item_row.base_price,
                markup_percent=item_row.markup_percent,
                markup_amount=0,
                source_store=item_row.source_store,
                source_address=item_row.source_address,
                sku=item_row.sku,
                barcode=item_row.barcode,
            )

            item = ConvenienceItemService.create_item(
                db=db,
                item_data=item_create,
                created_by_id=current_user.id
            )

            imported_items.append(item)
            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append({
                "row": idx + 1,
                "item_name": item_row.name,
                "error": str(e)
            })

    return ItemBulkImportResponse(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        imported_items=imported_items
    )


# Configuration Endpoints

@router.get("/venues/{venue_id}/config", response_model=ConvenienceStoreConfigResponse)
def get_venue_config(
    venue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get convenience store configuration for a venue.

    Creates a default configuration if one doesn't exist.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    return ConvenienceConfigService.get_or_create_config(db=db, venue_id=venue_id)


@router.put("/venues/{venue_id}/config", response_model=ConvenienceStoreConfigResponse)
def update_venue_config(
    venue_id: UUID,
    config_data: ConvenienceStoreConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update convenience store configuration.

    Only provided fields will be updated. This includes:
    - Feature enable/disable toggle
    - Service fee percentage
    - Order amount limits
    - Complimentary parking time
    - Operating hours
    - Welcome/instruction messages
    - Storage locations

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    return ConvenienceConfigService.update_config(
        db=db,
        venue_id=venue_id,
        config_data=config_data
    )


# Order Management Endpoints

@router.get("/venues/{venue_id}/orders", response_model=ConvenienceOrderList)
def list_venue_orders(
    venue_id: UUID,
    status: Optional[str] = Query(None, description="Filter by order status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Orders per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all convenience orders for a venue.

    Supports filtering by order status and pagination.
    Returns order summaries for list view.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    orders, total = ConvenienceOrderService.list_venue_orders(
        db=db,
        venue_id=venue_id,
        status=status,
        page=page,
        page_size=page_size
    )

    # Convert to summary format
    summaries = []
    for order in orders:
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


@router.get("/venues/{venue_id}/orders/{order_id}", response_model=ConvenienceOrderResponse)
def get_venue_order(
    venue_id: UUID,
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific order.

    Includes full order details, line items, events timeline, and customer information.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)

    # Verify order belongs to venue
    if order.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order


@router.patch("/venues/{venue_id}/orders/{order_id}/refund", response_model=ConvenienceOrderResponse)
def refund_order(
    venue_id: UUID,
    order_id: UUID,
    refund_data: OrderRefundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process a refund for an order.

    This marks the order as refunded and records the refund amount and reason.
    Note: Actual payment processing (Stripe refund) should be handled separately.

    Requires: venue_admin or super_admin role
    """
    check_admin_permissions(current_user, venue_id, db)

    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)

    # Verify order belongs to venue
    if order.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Validate refund amount
    if refund_data.refund_amount > order.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount cannot exceed order total"
        )

    # TODO: Implement actual refund logic with payment processor
    # For now, just update the order
    from app.models.convenience import ConvenienceOrder, ConvenienceOrderEvent, ConvenienceOrderStatus
    from uuid import uuid4
    from datetime import datetime

    db_order = db.query(ConvenienceOrder).filter(ConvenienceOrder.id == order_id).first()
    db_order.status = ConvenienceOrderStatus.REFUNDED.value
    db_order.refund_amount = refund_data.refund_amount
    db_order.refund_reason = refund_data.refund_reason

    # Log event
    event = ConvenienceOrderEvent(
        id=uuid4(),
        order_id=order_id,
        status=ConvenienceOrderStatus.REFUNDED.value,
        notes=f"Refund processed: ${refund_data.refund_amount} - {refund_data.refund_reason}",
        created_by_id=current_user.id,
    )
    db.add(event)

    db.commit()
    db.refresh(db_order)

    return ConvenienceOrderService.get_order(db=db, order_id=order_id)


@router.get("/categories", response_model=CategoriesResponse)
def get_categories(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of available item categories.

    Returns all possible category values that can be used when creating items.

    Requires: Any authenticated user
    """
    categories = [category.value for category in ConvenienceItemCategory]
    return CategoriesResponse(categories=categories)
