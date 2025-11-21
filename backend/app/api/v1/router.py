from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    parking,
    opportunities,
    partner_opportunities,
    valet,
    valet_staff,
    convenience,
    convenience_admin,
    convenience_staff,
    admin,
)


api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)

# Include user management routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)

# Include parking routes (public - no auth required)
api_router.include_router(
    parking.router,
    prefix="/parking",
    tags=["parking"],
)

# Include opportunity routes (requires user authentication)
api_router.include_router(
    opportunities.router,
    prefix="/opportunities",
    tags=["opportunities"],
)

# Include partner opportunity routes (requires partner API key)
api_router.include_router(
    partner_opportunities.router,
    prefix="/partner",
    tags=["partner-opportunities"],
)

# Include valet service routes (mixed auth - some public, some require auth)
api_router.include_router(
    valet.router,
    prefix="/valet",
    tags=["valet"],
)

# Include valet staff routes (requires staff authentication)
api_router.include_router(
    valet_staff.router,
    prefix="/valet/staff",
    tags=["valet-staff"],
)

# Include convenience store routes (customer-facing, mixed auth)
api_router.include_router(
    convenience.router,
    prefix="/convenience",
    tags=["convenience"],
)

# Include convenience store admin routes (requires admin authentication)
api_router.include_router(
    convenience_admin.router,
    prefix="/convenience/admin",
    tags=["convenience-admin"],
)

# Include convenience store staff routes (requires staff authentication)
api_router.include_router(
    convenience_staff.router,
    prefix="/convenience/staff",
    tags=["convenience-staff"],
)

# Include general admin routes (requires admin authentication)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
)
