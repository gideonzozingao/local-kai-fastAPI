from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictException, UnauthorizedException, BadRequestException
from app.models.models import User, UserRole
from app.schemas.user import UserRegister, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, data: UserRegister, role: UserRole = UserRole.CUSTOMER) -> TokenResponse:
        # Check existing user
        if self.user_repo.get_by_email(data.email):
            raise ConflictException("A user with this email already exists")

        if data.phone and self.user_repo.get_by_phone(data.phone):
            raise ConflictException("A user with this phone already exists")

        user = self.user_repo.create(
            email=data.email,
            full_name=data.full_name,
            password=data.password,
            phone=data.phone,
            role=role,
        )

        return self._generate_tokens(user)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is disabled. Contact support.")

        return self._generate_tokens(user)

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid or expired refresh token")

        user = self.user_repo.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        return self._generate_tokens(user)

    def change_password(self, user: User, current_password: str, new_password: str) -> dict:
        if not verify_password(current_password, user.password_hash):
            raise BadRequestException("Current password is incorrect")

        self.user_repo.update_password(user, new_password)
        return {"message": "Password changed successfully"}

    def _generate_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )
