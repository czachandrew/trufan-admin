from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time

from app.core.redis_client import redis_client
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""

    async def dispatch(self, request: Request, call_next):
        # Get client IP (handle TestClient which has no client attribute)
        client_ip = request.client.host if request.client else "testclient"

        # Create rate limit key
        minute_key = f"rate_limit:{client_ip}:{int(time.time() / 60)}"

        # Get current request count
        try:
            request_count = redis_client.incr(minute_key)

            # Set expiration on first request
            if request_count == 1:
                redis_client.expire(minute_key, 60)

            # Check if rate limit exceeded
            if request_count > settings.RATE_LIMIT_PER_MINUTE:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )

        except Exception as e:
            # If Redis is down, allow request to proceed
            pass

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, settings.RATE_LIMIT_PER_MINUTE - request_count)
        )

        return response
