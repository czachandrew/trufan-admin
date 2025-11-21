"""
Opportunity Engine - Core service for contextual opportunity discovery.

This is NOT an ad server. It's a value discovery system that matches users
with relevant opportunities based on their current context and preferences.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import uuid4
import secrets
import string
import math
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.opportunity import (
    Opportunity,
    OpportunityInteraction,
    OpportunityPreferences,
    InteractionType,
    FrequencyPreference,
)
from app.models.parking import ParkingSession
from app.models.user import User
from app.schemas.opportunity import (
    OpportunityResponse,
    OpportunityAcceptResponse,
    InteractionContext,
)


class UserContext:
    """Container for user's current context."""

    def __init__(
        self,
        user_id: Optional[str],
        parking_session_id: str,
        time_remaining_minutes: int,
        parking_rate_per_hour: Decimal,
        current_time: datetime,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        max_acceptable_distance: int = 500,
        preferences: Optional[OpportunityPreferences] = None,
    ):
        self.user_id = user_id
        self.parking_session_id = parking_session_id
        self.time_remaining_minutes = time_remaining_minutes
        self.parking_rate_per_hour = parking_rate_per_hour
        self.current_time = current_time
        self.user_lat = user_lat
        self.user_lng = user_lng
        self.max_acceptable_distance = max_acceptable_distance
        self.preferences = preferences


class OpportunityEngine:
    """
    Core engine for matching user contexts with relevant opportunities.
    This is NOT an ad server - it's a value discovery system.
    """

    def __init__(self, db: Session, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.max_opportunities_per_request = 3

    async def get_relevant_opportunities(
        self, user_id: Optional[str], parking_session_id: str
    ) -> List[OpportunityResponse]:
        """
        Find the most relevant opportunities for a user's current context.

        Relevance factors (in order of importance):
        1. User hasn't dismissed this category recently (authenticated only)
        2. Timing alignment with parking session
        3. Physical proximity (walkable distance)
        4. Available capacity
        5. User's historical preferences (authenticated only)
        6. Value score of the opportunity

        Args:
            user_id: Optional user ID. If None, shows public opportunities without
                    personalization or impression tracking.
            parking_session_id: Required parking session ID for context.
        """

        # Get parking session details
        session = await self._get_parking_session(parking_session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail="Parking session not found"
            )

        # For authenticated users, verify session ownership
        if user_id and session.user_id and str(session.user_id) != user_id:
            raise HTTPException(
                status_code=403, detail="Invalid session access"
            )

        # Get user preferences (or defaults for unauthenticated users)
        if user_id:
            preferences = await self._get_or_create_user_preferences(user_id)
            if not preferences.opportunities_enabled:
                return []
        else:
            # Default preferences for unauthenticated users
            preferences = OpportunityPreferences(
                user_id=None,  # No user ID for unauthenticated
                opportunities_enabled=True,
                frequency_preference=FrequencyPreference.OCCASIONAL.value,
                max_per_session=3,
                quiet_hours=[],
                no_opportunity_days=[],
                preferred_categories=[],
                blocked_categories=[],
                blocked_partner_ids=[],
                max_walking_distance_meters=500,
                acceptance_patterns={},
            )

        # Build context
        context = await self._build_user_context(user_id, session, preferences)

        # Get candidate opportunities
        candidates = await self._get_candidate_opportunities(context)

        # Score and rank
        scored = []
        for opportunity in candidates:
            score = await self._calculate_relevance_score(opportunity, context)
            if score > 0:
                scored.append((score, opportunity))

        # Sort by score and return top N
        scored.sort(key=lambda x: x[0], reverse=True)
        top_opportunities = [opp for _, opp in scored[:self.max_opportunities_per_request]]

        # Record impressions (only for authenticated users)
        if user_id:
            await self._record_impressions(user_id, parking_session_id, top_opportunities)

        # Convert to response objects with distance
        return [
            OpportunityResponse.from_orm_with_distance(
                opp, context.user_lat, context.user_lng
            )
            for opp in top_opportunities
        ]

    async def _get_parking_session(self, session_id: str) -> Optional[ParkingSession]:
        """Get parking session by ID."""
        return self.db.query(ParkingSession).filter(
            ParkingSession.id == session_id
        ).first()

    async def _get_or_create_user_preferences(
        self, user_id: str
    ) -> OpportunityPreferences:
        """Get or create user preferences with defaults."""
        preferences = self.db.query(OpportunityPreferences).filter(
            OpportunityPreferences.user_id == user_id
        ).first()

        if not preferences:
            # Create default preferences
            preferences = OpportunityPreferences(
                user_id=user_id,
                opportunities_enabled=True,
                frequency_preference=FrequencyPreference.OCCASIONAL.value,
                max_per_session=3,
                quiet_hours=[],
                no_opportunity_days=[],
                preferred_categories=[],
                blocked_categories=[],
                blocked_partner_ids=[],
                max_walking_distance_meters=500,
                acceptance_patterns={},
            )
            self.db.add(preferences)
            self.db.commit()

        return preferences

    async def _build_user_context(
        self, user_id: Optional[str], session: ParkingSession, preferences: OpportunityPreferences
    ) -> UserContext:
        """Build context object from parking session and preferences."""
        now = datetime.utcnow()
        time_remaining = 0
        if session.expires_at:
            time_remaining = int((session.expires_at - now).total_seconds() / 60)

        # Calculate effective parking rate
        parking_rate = Decimal("5.00")  # Default
        if session.base_price and session.start_time and session.expires_at:
            duration_hours = (session.expires_at - session.start_time).total_seconds() / 3600
            if duration_hours > 0:
                parking_rate = session.base_price / Decimal(str(duration_hours))

        # Get parking lot location for user position estimate
        user_lat = None
        user_lng = None
        if session.parking_lot and session.parking_lot.location_lat:
            user_lat = float(session.parking_lot.location_lat)
            user_lng = float(session.parking_lot.location_lng)

        return UserContext(
            user_id=user_id,
            parking_session_id=str(session.id),
            time_remaining_minutes=max(0, time_remaining),
            parking_rate_per_hour=parking_rate,
            current_time=now,
            user_lat=user_lat,
            user_lng=user_lng,
            max_acceptable_distance=preferences.max_walking_distance_meters,
            preferences=preferences,
        )

    async def _get_candidate_opportunities(
        self, context: UserContext
    ) -> List[Opportunity]:
        """Get opportunities that match basic criteria."""
        now = context.current_time

        query = self.db.query(Opportunity).filter(
            Opportunity.is_active == True,
            Opportunity.is_approved == True,
            Opportunity.valid_from <= now,
            Opportunity.valid_until >= now,
        )

        # Filter by capacity
        query = query.filter(
            or_(
                Opportunity.total_capacity.is_(None),
                Opportunity.used_capacity < Opportunity.total_capacity,
            )
        )

        # Filter by location if user location available
        if context.user_lat and context.user_lng:
            # Rough bounding box filter (before precise distance calc)
            # 1 degree ~111km, so 0.01 degree ~1km
            max_distance_degrees = context.max_acceptable_distance / 111000
            query = query.filter(
                Opportunity.location_lat.between(
                    Decimal(str(context.user_lat - max_distance_degrees)),
                    Decimal(str(context.user_lat + max_distance_degrees)),
                ),
                Opportunity.location_lng.between(
                    Decimal(str(context.user_lng - max_distance_degrees)),
                    Decimal(str(context.user_lng + max_distance_degrees)),
                ),
            )

        # Filter by blocked partners (only for authenticated users)
        if context.preferences and context.preferences.blocked_partner_ids:
            query = query.filter(
                ~Opportunity.partner_id.in_(context.preferences.blocked_partner_ids)
            )

        # Check cooldown - user hasn't seen this recently (only for authenticated users)
        if context.user_id:
            cooldown_cutoff = now - timedelta(hours=24)
            recent_interactions = (
                self.db.query(OpportunityInteraction.opportunity_id)
                .filter(
                    OpportunityInteraction.user_id == context.user_id,
                    OpportunityInteraction.created_at >= cooldown_cutoff,
                    OpportunityInteraction.interaction_type.in_([
                        InteractionType.DISMISSED.value,
                        InteractionType.ACCEPTED.value,
                    ]),
                )
                .all()
            )
            recent_opp_ids = [opp_id for (opp_id,) in recent_interactions]
            if recent_opp_ids:
                query = query.filter(~Opportunity.id.in_(recent_opp_ids))

        return query.all()

    async def _calculate_relevance_score(
        self, opportunity: Opportunity, context: UserContext
    ) -> float:
        """
        Calculate relevance score for an opportunity.
        Returns 0-100, where 100 is perfect relevance.
        """

        score = 0.0

        # Temporal relevance (0-30 points)
        time_score = self._calculate_temporal_relevance(
            opportunity.trigger_rules,
            context.time_remaining_minutes,
            context.current_time,
        )
        score += time_score * 30

        # Spatial proximity (0-25 points)
        if context.user_lat and context.user_lng and opportunity.location_lat:
            distance_score = self._calculate_distance_score(
                float(opportunity.location_lat),
                float(opportunity.location_lng),
                context.user_lat,
                context.user_lng,
                context.max_acceptable_distance,
            )
            score += distance_score * 25
        else:
            # No location data, give partial score
            score += 12.5

        # Value alignment (0-20 points)
        value_score = self._calculate_value_score(
            opportunity.value_details, context.parking_rate_per_hour
        )
        score += value_score * 20

        # Capacity urgency (0-15 points)
        if opportunity.total_capacity:
            remaining_pct = (
                opportunity.total_capacity - opportunity.used_capacity
            ) / opportunity.total_capacity
            if remaining_pct < 0.2:  # Less than 20% remaining
                score += 15
            elif remaining_pct < 0.5:
                score += 10
        else:
            score += 5  # Unlimited capacity gets partial points

        # User affinity (0-10 points)
        affinity_score = await self._calculate_user_affinity(
            context.user_id,
            opportunity.opportunity_type,
            str(opportunity.partner_id),
        )
        score += affinity_score * 10

        return min(score, 100)  # Cap at 100

    def _calculate_temporal_relevance(
        self,
        trigger_rules: Dict[str, Any],
        time_remaining_minutes: int,
        current_time: datetime,
    ) -> float:
        """Calculate how well opportunity timing matches context. Returns 0-1."""

        score = 1.0

        # Check parking duration remaining
        duration_min = trigger_rules.get("time_remaining_min")
        duration_max = trigger_rules.get("time_remaining_max")

        if duration_min and time_remaining_minutes < duration_min:
            score *= 0.5
        if duration_max and time_remaining_minutes > duration_max:
            score *= 0.5

        # Check day of week
        days_of_week = trigger_rules.get("days_of_week", [])
        if days_of_week:
            current_day = current_time.strftime("%A").lower()
            if current_day not in [d.lower() for d in days_of_week]:
                score *= 0.7

        # Check time of day
        time_start = trigger_rules.get("time_of_day_start")
        time_end = trigger_rules.get("time_of_day_end")
        if time_start and time_end:
            current_time_str = current_time.strftime("%H:%M")
            if not (time_start <= current_time_str <= time_end):
                score *= 0.7

        return score

    def _calculate_distance_score(
        self,
        opp_lat: float,
        opp_lng: float,
        user_lat: float,
        user_lng: float,
        max_distance: int,
    ) -> float:
        """Calculate distance score. Returns 0-1."""

        # Calculate distance using Haversine formula
        R = 6371000  # Earth radius in meters

        lat1, lng1 = math.radians(user_lat), math.radians(user_lng)
        lat2, lng2 = math.radians(opp_lat), math.radians(opp_lng)

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c

        if distance > max_distance:
            return 0.0

        # Closer is better - linear decay
        return 1.0 - (distance / max_distance)

    def _calculate_value_score(
        self, value_details: Dict[str, Any], parking_rate_per_hour: Decimal
    ) -> float:
        """Calculate value score based on offer benefits. Returns 0-1."""

        score = 0.0

        # Discount value
        discount_pct = value_details.get("discount_percentage", 0)
        discount_amt = value_details.get("discount_amount", 0)

        if discount_pct >= 50:
            score += 0.5
        elif discount_pct >= 25:
            score += 0.35
        elif discount_pct >= 10:
            score += 0.2

        if discount_amt >= 20:
            score += 0.3
        elif discount_amt >= 10:
            score += 0.2
        elif discount_amt >= 5:
            score += 0.1

        # Parking extension value
        parking_ext_min = value_details.get("parking_extension_minutes", 0)
        if parking_ext_min > 0:
            # Compare to user's parking cost
            extension_hours = parking_ext_min / 60
            extension_value = float(parking_rate_per_hour) * extension_hours
            if extension_value >= 10:
                score += 0.3
            elif extension_value >= 5:
                score += 0.2
            else:
                score += 0.1

        # Perks
        perks = value_details.get("perks", [])
        if len(perks) >= 3:
            score += 0.2
        elif len(perks) >= 1:
            score += 0.1

        return min(score, 1.0)

    async def _calculate_user_affinity(
        self, user_id: str, opportunity_type: str, partner_id: str
    ) -> float:
        """Calculate user's historical affinity for this type/partner. Returns 0-1."""

        # Get user's past interactions
        interactions = (
            self.db.query(OpportunityInteraction)
            .join(Opportunity)
            .filter(
                OpportunityInteraction.user_id == user_id,
                OpportunityInteraction.interaction_type.in_([
                    InteractionType.ACCEPTED.value,
                    InteractionType.COMPLETED.value,
                ]),
            )
            .limit(50)
            .all()
        )

        if not interactions:
            return 0.5  # Neutral for new users

        # Calculate acceptance rate for this type
        type_matches = sum(
            1 for i in interactions
            if i.opportunity and i.opportunity.opportunity_type == opportunity_type
        )
        type_score = type_matches / len(interactions)

        # Calculate acceptance rate for this partner
        partner_matches = sum(
            1 for i in interactions
            if i.opportunity and str(i.opportunity.partner_id) == partner_id
        )
        partner_score = partner_matches / len(interactions) if partner_matches else 0

        # Weighted average
        return (type_score * 0.7) + (partner_score * 0.3)

    async def _record_impressions(
        self, user_id: str, session_id: str, opportunities: List[Opportunity]
    ):
        """Record that opportunities were shown to user."""

        for opp in opportunities:
            interaction = OpportunityInteraction(
                user_id=user_id,
                opportunity_id=opp.id,
                parking_session_id=session_id,
                interaction_type=InteractionType.IMPRESSED.value,
                interaction_context={},
                created_at=datetime.utcnow(),
            )
            self.db.add(interaction)

        self.db.commit()

    async def accept_opportunity(
        self, user_id: str, opportunity_id: str, parking_session_id: str
    ) -> OpportunityAcceptResponse:
        """
        Process user accepting an opportunity.
        Returns claim details for the user.
        """

        # Verify opportunity is still available
        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id
        ).first()

        if not opportunity or not opportunity.is_available:
            raise HTTPException(
                status_code=410, detail="Opportunity no longer available"
            )

        # Generate claim code
        claim_code = self._generate_claim_code()

        # Calculate parking extension value if applicable
        parking_extended_by = opportunity.value_details.get("parking_extension_minutes")

        # Check if interaction already exists (from impression)
        existing_interaction = self.db.query(OpportunityInteraction).filter(
            OpportunityInteraction.user_id == user_id,
            OpportunityInteraction.opportunity_id == opportunity_id,
            OpportunityInteraction.parking_session_id == parking_session_id
        ).first()

        if existing_interaction:
            # Update existing interaction
            existing_interaction.interaction_type = InteractionType.ACCEPTED.value
            existing_interaction.interaction_context = await self._get_current_context(parking_session_id)
            existing_interaction.value_claimed = opportunity.value_details
            interaction = existing_interaction
        else:
            # Create new interaction
            interaction = OpportunityInteraction(
                user_id=user_id,
                opportunity_id=opportunity_id,
                parking_session_id=parking_session_id,
                interaction_type=InteractionType.ACCEPTED.value,
                interaction_context=await self._get_current_context(parking_session_id),
                value_claimed=opportunity.value_details,
                created_at=datetime.utcnow(),
            )
            self.db.add(interaction)

        # Store claim code in interaction context
        if not interaction.interaction_context:
            interaction.interaction_context = {}
        interaction.interaction_context['claim_code'] = claim_code

        # Update capacity
        if opportunity.total_capacity:
            opportunity.used_capacity += 1

        # Apply parking extension if included
        if parking_extended_by:
            await self._extend_parking_session(parking_session_id, parking_extended_by)

        self.db.commit()

        # TODO: Notify partner via webhook (integrate with notification service)

        return OpportunityAcceptResponse(
            success=True,
            claim_code=claim_code,
            instructions=self._format_claim_instructions(opportunity),
            valid_until=(datetime.utcnow() + timedelta(hours=24)),
            parking_extended_by=parking_extended_by,
        )

    def _generate_claim_code(self, length: int = 8) -> str:
        """Generate unique claim code."""
        alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def _get_current_context(self, parking_session_id: str) -> Dict[str, Any]:
        """Get current context for interaction recording."""
        session = await self._get_parking_session(parking_session_id)
        if not session:
            return {}

        now = datetime.utcnow()
        time_remaining = 0
        if session.expires_at:
            time_remaining = int((session.expires_at - now).total_seconds() / 60)

        return {
            "parking_time_remaining": time_remaining,
            "time_of_day": now.strftime("%H:%M"),
        }

    def _format_claim_instructions(self, opportunity: Opportunity) -> str:
        """Format instructions for claiming the opportunity."""
        return (
            f"Show this code to the staff at {opportunity.address or 'the location'}: "
            f"Your offer: {opportunity.value_proposition}"
        )

    async def _extend_parking_session(self, session_id: str, minutes: int):
        """Extend parking session expiration time."""
        session = await self._get_parking_session(session_id)
        if session and session.expires_at:
            session.expires_at = session.expires_at + timedelta(minutes=minutes)
            self.db.commit()

    async def dismiss_opportunity(
        self, user_id: str, opportunity_id: str, parking_session_id: str, reason: str, feedback: Optional[str] = None
    ):
        """Record opportunity dismissal."""
        interaction = OpportunityInteraction(
            user_id=user_id,
            opportunity_id=opportunity_id,
            parking_session_id=parking_session_id,
            interaction_type=InteractionType.DISMISSED.value,
            interaction_context={
                "dismiss_reason": reason,
                "feedback": feedback,
            },
            created_at=datetime.utcnow(),
        )
        self.db.add(interaction)
        self.db.commit()

    async def get_user_interaction_history(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[OpportunityInteraction]:
        """Get user's opportunity interaction history."""
        return (
            self.db.query(OpportunityInteraction)
            .filter(OpportunityInteraction.user_id == user_id)
            .order_by(OpportunityInteraction.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
