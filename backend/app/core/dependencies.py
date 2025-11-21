from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole


security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials

    # Verify token
    payload = verify_token(token, token_type="access")
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current authenticated user (optional - returns None if not authenticated)."""
    if not credentials:
        return None

    token = credentials.credentials

    # Verify token
    try:
        payload = verify_token(token, token_type="access")
        user_id = payload.get("sub")

        if not user_id:
            return None

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            return None

        return user
    except Exception:
        return None


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(required_role: UserRole):
    """Dependency to require specific user role."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Role hierarchy
        role_hierarchy = {
            UserRole.CUSTOMER: 0,
            UserRole.VENUE_STAFF: 1,
            UserRole.VENUE_ADMIN: 2,
            UserRole.SUPER_ADMIN: 3,
        }

        user_role_level = role_hierarchy.get(current_user.role, 0)
        required_role_level = role_hierarchy.get(required_role, 0)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker
