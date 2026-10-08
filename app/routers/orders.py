from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, col, select

from app.database import SessionDep
from app.models import Order, OrderCreate, OrderPublic, OrderUpdate
from app.routers.users import get_active_user

router = APIRouter(prefix="/orders", tags=["orders"])


def get_active_order(session: Session, order_id: int) -> Order:
    order = session.get(Order, order_id)
    if order is None or order.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", status_code=201)
def create_order(order: OrderCreate, session: SessionDep) -> OrderPublic:
    # SQLite doesn't enforce the foreign key, so check the user exists here.
    get_active_user(session, order.user_id)
    db_order = Order.model_validate(order)
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order


@router.get("/")
def list_orders(
    user_id: int,
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[OrderPublic]:
    statement = (
        select(Order)
        .where(Order.user_id == user_id, col(Order.deleted_at).is_(None))
        .offset(offset)
        .limit(limit)
    )
    return session.exec(statement).all()


@router.get("/{order_id}")
def get_order(order_id: int, session: SessionDep) -> OrderPublic:
    return get_active_order(session, order_id)


@router.patch("/{order_id}")
def update_order(
    order_id: int, order: OrderUpdate, session: SessionDep
) -> OrderPublic:
    db_order = get_active_order(session, order_id)
    db_order.sqlmodel_update(order.model_dump(exclude_unset=True, exclude_none=True))
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, session: SessionDep) -> None:
    order = get_active_order(session, order_id)
    order.deleted_at = datetime.now(UTC)
    session.add(order)
    session.commit()


# TODO: restrict access once the auth service exists
