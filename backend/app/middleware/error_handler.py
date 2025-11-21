from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from app.core.logging_config import get_correlation_id


logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    correlation_id = get_correlation_id()

    logger.error(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={"correlation_id": correlation_id},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "correlation_id": correlation_id,
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    correlation_id = get_correlation_id()

    logger.warning(
        f"Validation Error: {exc.errors()}",
        extra={"correlation_id": correlation_id},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation error",
                "details": exc.errors(),
                "correlation_id": correlation_id,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    correlation_id = get_correlation_id()

    logger.exception(
        f"Unhandled Exception: {str(exc)}",
        extra={"correlation_id": correlation_id},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
                "correlation_id": correlation_id,
            }
        },
    )
