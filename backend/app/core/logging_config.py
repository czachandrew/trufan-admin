import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from app.core.config import settings


# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record):
        record.correlation_id = correlation_id.get() or "no-correlation-id"
        return True


def setup_logging():
    """Configure application logging."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Create formatter with correlation ID
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIdFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_correlation_id() -> str:
    """Get or create correlation ID."""
    corr_id = correlation_id.get()
    if not corr_id:
        corr_id = str(uuid.uuid4())
        correlation_id.set(corr_id)
    return corr_id


def set_correlation_id(corr_id: str):
    """Set correlation ID."""
    correlation_id.set(corr_id)
