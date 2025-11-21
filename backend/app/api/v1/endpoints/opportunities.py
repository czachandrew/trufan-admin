"""
Public API endpoints for opportunities.
Users can discover, accept, and manage opportunities.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.opportunity import OpportunityPreferences
from app.schemas.opportunity import (
    OpportunityResponse,
    OpportunityAccept,
    OpportunityDismiss,
    OpportunityAcceptResponse,
    OpportunityInteractionResponse,
    OpportunityPreferencesUpdate,
    OpportunityPreferencesResponse,
)
from app.services.opportunity_engine import OpportunityEngine


router = APIRouter()


@router.get("/active", response_model=List[OpportunityResponse])
async def get_active_opportunities(
    session_id: UUID = Query(..., description="Parking session ID"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Get relevant opportunities for current context.

    Returns max 3 opportunities perfectly matched to the parking session,
    location, and user preferences (if authenticated).

    This is NOT an ad endpoint - it's a value discovery system.

    Authentication is optional - unauthenticated users can browse opportunities
    but must create an account to accept them.
    """
    engine = OpportunityEngine(db)

    # Pass user_id as optional - None for unauthenticated users
    user_id = str(current_user.id) if current_user else None

    opportunities = await engine.get_relevant_opportunities(
        user_id,
        str(session_id)
    )

    return opportunities


@router.get("/history", response_model=List[OpportunityInteractionResponse])
async def get_opportunity_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, regex="^(accepted|completed|dismissed)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get your opportunity interaction history.

    Includes accepted, completed, and dismissed opportunities.
    """
    from app.models.opportunity import OpportunityInteraction

    query = db.query(OpportunityInteraction).filter(
        OpportunityInteraction.user_id == current_user.id
    )

    if status_filter:
        query = query.filter(
            OpportunityInteraction.interaction_type == status_filter
        )

    interactions = query.order_by(
        OpportunityInteraction.created_at.desc()
    ).offset(offset).limit(limit).all()

    return interactions


@router.get("/preferences", response_model=OpportunityPreferencesResponse)
async def get_opportunity_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get your opportunity preferences.

    Control what opportunities you see, when, and how often.
    """
    preferences = db.query(OpportunityPreferences).filter(
        OpportunityPreferences.user_id == current_user.id
    ).first()

    if not preferences:
        # Create default preferences
        engine = OpportunityEngine(db)
        preferences = await engine._get_or_create_user_preferences(str(current_user.id))

    return preferences


@router.put("/preferences", response_model=OpportunityPreferencesResponse)
async def update_opportunity_preferences(
    preferences_data: OpportunityPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update your opportunity preferences.

    Full control over:
    - Master enable/disable
    - Frequency (all, occasional, minimal)
    - Quiet hours
    - Category preferences
    - Walking distance
    - Blocked partners
    """
    preferences = db.query(OpportunityPreferences).filter(
        OpportunityPreferences.user_id == current_user.id
    ).first()

    if not preferences:
        engine = OpportunityEngine(db)
        preferences = await engine._get_or_create_user_preferences(str(current_user.id))

    # Update fields
    update_dict = preferences_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            if field == 'frequency_preference' and value:
                setattr(preferences, field, value.value)
            else:
                setattr(preferences, field, value)

    from datetime import datetime
    preferences.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(preferences)

    return preferences


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity_details(
    opportunity_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific opportunity.
    """
    from app.models.opportunity import Opportunity

    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.is_active == True,
        Opportunity.is_approved == True
    ).first()

    if not opportunity:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    # Record view interaction if user is authenticated
    if current_user:
        from app.models.opportunity import OpportunityInteraction, InteractionType
        from datetime import datetime

        view_interaction = OpportunityInteraction(
            user_id=current_user.id,
            opportunity_id=opportunity_id,
            interaction_type=InteractionType.VIEWED.value,
            created_at=datetime.utcnow()
        )
        db.add(view_interaction)
        db.commit()

    return OpportunityResponse.from_orm_with_distance(opportunity)


@router.post("/{opportunity_id}/accept", response_model=OpportunityAcceptResponse)
async def accept_opportunity(
    opportunity_id: UUID,
    accept_data: OpportunityAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept an opportunity and receive a claim code.

    The user will receive:
    - A unique claim code to show at the partner location
    - Instructions on how to redeem
    - Any immediate benefits (e.g., parking extension)
    """
    engine = OpportunityEngine(db)

    result = await engine.accept_opportunity(
        str(current_user.id),
        str(opportunity_id),
        str(accept_data.parking_session_id)
    )

    return result


@router.post("/{opportunity_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_opportunity(
    opportunity_id: UUID,
    dismiss_data: OpportunityDismiss,
    session_id: UUID = Query(..., description="Parking session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dismiss an opportunity with feedback.

    This helps us learn your preferences and avoid showing
    irrelevant opportunities in the future.
    """
    engine = OpportunityEngine(db)

    await engine.dismiss_opportunity(
        str(current_user.id),
        str(opportunity_id),
        str(session_id),
        dismiss_data.reason,
        dismiss_data.feedback
    )

    return None
