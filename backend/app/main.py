from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)


# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.

    Returns the status of the API service.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint.

    Returns basic API information.
    """
    return {
        "message": "Welcome to TruFan API",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    import logging
    from app.services.background_tasks import BackgroundTasks

    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Start background tasks for parking system
    BackgroundTasks.start_expiration_checker(check_interval_minutes=5)
    BackgroundTasks.start_expired_session_cleanup(check_interval_minutes=10)
    logger.info("Started parking background tasks")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    import logging
    from app.services.background_tasks import BackgroundTasks

    logger = logging.getLogger(__name__)
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

    # Stop background tasks
    await BackgroundTasks.stop_expiration_checker()
    logger.info("Stopped parking background tasks")

    # Close Redis connection
    from app.core.redis_client import redis_client

    redis_client.close()
