from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.schemas.user import UserResponse


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[UUID] = None
    exp: Optional[int] = None
    type: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class AuthResponse(BaseModel):
    """Schema for authentication response including user data."""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
