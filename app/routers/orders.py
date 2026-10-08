from fastapi import APIRouter, HTTPException

from app.database import SessionDep
from app.models import Order, OrderPublic

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}")
def get_order(order_id: int, session: SessionDep) -> OrderPublic:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# TODO: create order, list orders by user
# TODO: restrict access once the auth service exists
