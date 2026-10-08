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
    body = response.json()
    assert body == {"id": body["id"], "name": "Ada", "email": "ada@example.com"}
    assert client.get(f"/users/{body['id']}").json() == body


def test_create_user_duplicate_email(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email="taken@example.com")

    response = client.post("/users/", json={"name": "Ada", "email": "taken@example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_list_users_excludes_deleted(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    kept = make_user(name="Kept", email="kept@example.com")
    gone = make_user(name="Gone", email="gone@example.com")
    client.delete(f"/users/{gone.id}")

    response = client.get("/users/")

    assert response.status_code == 200
    assert response.json() == [
        {"id": kept.id, "name": "Kept", "email": "kept@example.com"}
    ]


def test_update_user_name_only(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    user = make_user(name="Old", email="old@example.com")

    response = client.patch(f"/users/{user.id}", json={"name": "New"})

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": "New", "email": "old@example.com"}


def test_update_user_email(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user(name="Same", email="old@example.com")

    response = client.patch(f"/users/{user.id}", json={"email": "new@example.com"})

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "name": "Same", "email": "new@example.com"}


def test_update_user_email_conflict(
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
    client: TestClient,
    make_user: Callable[..., User],
    make_order: Callable[..., Order],
) -> None:
    user = make_user()
    make_order(user=user)

    response = client.delete(f"/users/{user.id}")

    assert response.status_code == 409
    assert response.json() == {"detail": "User has active orders"}
