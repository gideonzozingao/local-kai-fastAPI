from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate, UserAdminResponse
from app.schemas.restaurant import AddressCreate, AddressResponse
from app.models.models import User, Address
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user).model_dump()


@router.patch("/me")
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.update(current_user, **data.model_dump(exclude_none=True))
    return UserResponse.model_validate(user).model_dump()


# ─────────────────────────── Addresses ────────────────────────────

@router.get("/me/addresses")
def get_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return [AddressResponse.model_validate(a).model_dump() for a in addresses]


@router.post("/me/addresses", status_code=201)
def add_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    address = Address(user_id=current_user.id, **data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return AddressResponse.model_validate(address).model_dump()


@router.delete("/me/addresses/{address_id}")
def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = db.query(Address).filter(
        Address.id == address_id, Address.user_id == current_user.id
    ).first()
    if not address:
        raise NotFoundException("Address")
    db.delete(address)
    db.commit()
    return {"message": "Address deleted"}


# ─────────────────────────── Admin ────────────────────────────

@router.get("", dependencies=[Depends(require_admin)])
def list_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    users = UserRepository(db).get_all(skip, limit)
    return [UserAdminResponse.model_validate(u).model_dump() for u in users]


@router.get("/{user_id}", dependencies=[Depends(require_admin)])
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotFoundException("User")
    return UserAdminResponse.model_validate(user).model_dump()


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
def deactivate_user(user_id: str, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User")
    repo.deactivate(user)
    return {"message": "User deactivated"}