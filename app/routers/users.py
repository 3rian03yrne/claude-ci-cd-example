from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.database import SessionDep
from app.models import Order, User, UserCreate, UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def get_active_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _ensure_email_available(
    session: Session, email: str, exclude_id: int | None = None
) -> None:
    statement = select(User).where(
        User.email == email, col(User.deleted_at).is_(None)
    )
    if exclude_id is not None:
        statement = statement.where(User.id != exclude_id)
    if session.exec(statement).first() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")


def _commit_user(session: Session, user: User) -> None:
    # The pre-check can race with a concurrent write; the unique index is the
    # final word.
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    session.refresh(user)


@router.post("/", status_code=201)
def create_user(user: UserCreate, session: SessionDep) -> UserPublic:
    _ensure_email_available(session, user.email)
    db_user = User.model_validate(user)
    session.add(db_user)
    _commit_user(session, db_user)
    return db_user


@router.get("/")
def list_users(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[UserPublic]:
    statement = (
        select(User)
        .where(col(User.deleted_at).is_(None))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/{user_id}")
def get_user(user_id: int, session: SessionDep) -> UserPublic:
    return get_active_user(session, user_id)


@router.patch("/{user_id}")
def update_user(user_id: int, user: UserUpdate, session: SessionDep) -> UserPublic:
    db_user = get_active_user(session, user_id)
    data = user.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in data:
        _ensure_email_available(session, data["email"], exclude_id=user_id)
    db_user.sqlmodel_update(data)
    session.add(db_user)
    _commit_user(session, db_user)
    return db_user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, session: SessionDep) -> None:
    user = get_active_user(session, user_id)
    active_order = session.exec(
        select(Order).where(
            Order.user_id == user_id, col(Order.deleted_at).is_(None)
        )
    ).first()
    if active_order is not None:
        raise HTTPException(status_code=409, detail="User has active orders")
    user.deleted_at = datetime.now(UTC)
    session.add(user)
    session.commit()
