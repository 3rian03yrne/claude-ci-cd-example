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


def test_create_order(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user()

    response = client.post(
        "/orders/",
        json={"item": "Gizmo", "quantity": 3, "total": "9.90", "user_id": user.id},
    )

    assert response.status_code == 201
    body = response.json()
    created_at = body.pop("created_at")
    assert body == {
        "id": 1,
        "item": "Gizmo",
        "quantity": 3,
        "total": "9.90",
        "status": "pending",
        "user_id": user.id,
    }
    assert datetime.fromisoformat(created_at)


def test_create_order_user_not_found(client: TestClient) -> None:
    response = client.post(
        "/orders/",
        json={"item": "Gizmo", "quantity": 3, "total": "9.90", "user_id": 999},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_list_orders_only_for_user(
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    other = make_user()
    mine = make_order(user=user, item="Mine")
    make_order(user=other, item="Theirs")

    response = client.get("/orders/", params={"user_id": user.id})

    assert response.status_code == 200
    body = response.json()
    assert [o["id"] for o in body] == [mine.id]
    assert body[0]["item"] == "Mine"


def test_list_orders_excludes_deleted(
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    kept = make_order(user=user)
    deleted = make_order(user=user)
    client.delete(f"/orders/{deleted.id}")

    response = client.get("/orders/", params={"user_id": user.id})

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [kept.id]


def test_list_orders_offset_and_limit(
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    orders = [make_order(user=user) for _ in range(3)]

    response = client.get(
        "/orders/", params={"user_id": user.id, "offset": 1, "limit": 1}
    )

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [orders[1].id]


def test_update_order(
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    order = make_order(user=user, item="Widget", quantity=2, total=Decimal("12.50"))

    response = client.patch(
        f"/orders/{order.id}", json={"quantity": 5, "status": "shipped"}
    )

    assert response.status_code == 200
    body = response.json()
    body.pop("created_at")
    assert body == {
        "id": order.id,
        "item": "Widget",
        "quantity": 5,
        "total": "12.50",
        "status": "shipped",
        "user_id": user.id,
    }



def test_delete_order(
    client: TestClient, make_order: Callable[..., Order]
) -> None:
    order = make_order()

    response = client.delete(f"/orders/{order.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/orders/{order.id}").status_code == 404
