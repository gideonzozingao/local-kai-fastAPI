from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.models import User, UserRole
from app.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_all(self, skip: int = 0, limit: int = 20) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def count(self) -> int:
        return self.db.query(User).count()

    def create(self, email: str, full_name: str, password: str,
               phone: Optional[str] = None, role: UserRole = UserRole.CUSTOMER) -> User:
        user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            password_hash=get_password_hash(password),
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, new_password: str) -> User:
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, user: User) -> User:
        user.is_active = False
        self.db.commit()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
