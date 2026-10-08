from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models import Order, User


def test_get_user(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user(name="William Blake", email="will@example.com")

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "name": "William Blake",
        "email": "will@example.com",
    }


def test_get_user_not_found(client: TestClient) -> None:
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_get_user_invalid_id(client: TestClient) -> None:
    response = client.get("/users/abc")

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == "int_parsing"
    assert error["loc"] == ["path", "user_id"]


def test_create_user(client: TestClient) -> None:
    response = client.post("/users/", json={"name": "Ada", "email": "ada@example.com"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Ada", "email": "ada@example.com"}


def test_list_users(client: TestClient, make_user: Callable[..., User]) -> None:
    first = make_user(name="Ann", email="ann@example.com")
    second = make_user(name="Bob", email="bob@example.com")

    response = client.get("/users/")

    assert response.status_code == 200
    assert response.json() == [
        {"id": first.id, "name": "Ann", "email": "ann@example.com"},
        {"id": second.id, "name": "Bob", "email": "bob@example.com"},
    ]


def test_update_user_email(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user(name="Ann", email="ann@example.com")

    response = client.patch(f"/users/{user.id}", json={"email": "new@example.com"})

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": "Ann", "email": "new@example.com"}


def test_update_user_name_only(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    user = make_user(name="Ann", email="ann@example.com")

    response = client.patch(f"/users/{user.id}", json={"name": "Anna"})

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": "Anna", "email": "ann@example.com"}


def test_delete_user(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user()

    response = client.delete(f"/users/{user.id}")

    assert response.status_code == 204
    assert client.get(f"/users/{user.id}").status_code == 404


def test_delete_user_with_active_orders(
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    make_order(user=user)

    response = client.delete(f"/users/{user.id}")

    assert response.status_code == 409
    assert response.json() == {"detail": "User has active orders"}
