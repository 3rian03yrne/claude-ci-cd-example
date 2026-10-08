from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.models import Order, User


def test_get_order(
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    order = make_order(user=user, item="Gizmo", quantity=3, total=Decimal("9.90"))

    response = client.get(f"/orders/{order.id}")

    assert response.status_code == 200
    body = response.json()
    created_at = body.pop("created_at")
    assert body == {
        "id": order.id,
        "item": "Gizmo",
        "quantity": 3,
        # Decimals serialize as strings, keeping both decimal places.
        "total": "9.90",
        "status": "pending",
        "user_id": user.id,
    }
    assert datetime.fromisoformat(created_at) == order.created_at


def test_get_order_not_found(client: TestClient) -> None:
    response = client.get("/orders/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Order not found"}


def test_get_order_invalid_id(client: TestClient) -> None:
    response = client.get("/orders/abc")

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == "int_parsing"
    assert error["loc"] == ["path", "order_id"]
