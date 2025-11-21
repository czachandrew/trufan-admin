from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import (
    UserCreate,
    UserLogin,
    PasswordReset,
    PasswordResetConfirm,
    PasswordChange,
)
from app.schemas.auth import AuthResponse, RefreshTokenRequest, Token
from app.services.auth_service import AuthService
from app.models.user import User


router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Minimum 8 characters, must contain digit and uppercase letter
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    """
    # Register user
    user = AuthService.register_user(db, user_data)

    # Create tokens
    tokens = AuthService.create_tokens(str(user.id))

    return AuthResponse(
        user=user,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
    )


@router.post("/login", response_model=AuthResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.

    Returns user profile and authentication tokens.
    """
    # Authenticate user
    user = AuthService.authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create tokens
    tokens = AuthService.create_tokens(str(user.id))

    return AuthResponse(
        user=user,
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Returns a new access token.
    """
    result = AuthService.refresh_access_token(db, refresh_data.refresh_token)

    return Token(
        access_token=result["access_token"],
        refresh_token=refresh_data.refresh_token,
        token_type=result["token_type"],
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.

    Invalidates the refresh token.
    """
    AuthService.logout(str(current_user.id))
    return None


@router.post("/password-reset/request")
def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db),
):
    """
    Request password reset.

    Sends password reset email if account exists.
    """
    message = AuthService.request_password_reset(db, reset_data.email)
    return {"message": message}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirm password reset with token.

    Resets password using the token sent via email.
    """
    message = AuthService.reset_password(db, reset_data.token, reset_data.new_password)
    return {"message": message}


@router.post("/password/change")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change password for authenticated user.

    Requires current password for verification.
    """
    message = AuthService.change_password(
        db,
        str(current_user.id),
        password_data.current_password,
        password_data.new_password,
    )
    return {"message": message}
