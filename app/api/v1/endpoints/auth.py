from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse,
    RefreshTokenRequest, ChangePasswordRequest, UserResponse,
)
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new customer account."""
    result = AuthService(db).register(data)
    return result.model_dump()


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login and receive access + refresh tokens."""
    result = AuthService(db).login(data.email, data.password)
    return result.model_dump()


@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new token pair."""
    result = AuthService(db).refresh_token(data.refresh_token)
    return result.model_dump()


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user).model_dump()


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password."""
    return AuthService(db).change_password(current_user, data.current_password, data.new_password)