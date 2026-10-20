from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models import Order, User
from app.routers import users


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


def test_create_user_duplicate_email(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email="dup@example.com")

    response = client.post("/users/", json={"name": "Other", "email": "dup@example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_create_user_email_race(
    client: TestClient,
    make_user: Callable[..., User],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_user(email="dup@example.com")
    monkeypatch.setattr(users, "_ensure_email_available", lambda *args, **kwargs: None)

    response = client.post("/users/", json={"name": "Other", "email": "dup@example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_list_users_offset_and_limit(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(name="A", email="a@example.com")
    second = make_user(name="B", email="b@example.com")
    make_user(name="C", email="c@example.com")

    response = client.get("/users/", params={"offset": 1, "limit": 1})

    assert response.status_code == 200
    assert response.json() == [{"id": second.id, "name": "B", "email": "b@example.com"}]


def test_update_user_name(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user(name="Old", email="old@example.com")

    response = client.patch(f"/users/{user.id}", json={"name": "New"})

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": "New", "email": "old@example.com"}


def test_update_user_email_taken(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email="taken@example.com")
    user = make_user(email="mine@example.com")

    response = client.patch(f"/users/{user.id}", json={"email": "taken@example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_delete_user(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user()

    response = client.delete(f"/users/{user.id}")

    assert response.status_code == 204
    assert client.get(f"/users/{user.id}").status_code == 404


def test_delete_user_with_active_order(
    client: TestClient, make_order: Callable[..., Order]
) -> None:
    order = make_order()

    response = client.delete(f"/users/{order.user_id}")

    assert response.status_code == 409
    assert response.json() == {"detail": "User has active orders"}
