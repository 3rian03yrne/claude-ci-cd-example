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
    assert isinstance(body["id"], int)
    assert body == {"id": body["id"], "name": "Ada", "email": "ada@example.com"}


def test_create_user_duplicate_email(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email="dup@example.com")

    response = client.post(
        "/users/", json={"name": "Other", "email": "dup@example.com"}
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_create_user_email_of_deleted_user(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    user = make_user(email="again@example.com")
    client.delete(f"/users/{user.id}")

    response = client.post(
        "/users/", json={"name": "New", "email": "again@example.com"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {"id": body["id"], "name": "New", "email": "again@example.com"}
    assert body["id"] != user.id


def test_list_users_excludes_deleted_and_paginates(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    first = make_user(name="First", email="first@example.com")
    gone = make_user(name="Gone", email="gone@example.com")
    third = make_user(name="Third", email="third@example.com")
    client.delete(f"/users/{gone.id}")

    all_response = client.get("/users/")
    page_response = client.get("/users/", params={"offset": 1, "limit": 1})

    assert all_response.status_code == 200
    assert all_response.json() == [
        {"id": first.id, "name": "First", "email": "first@example.com"},
        {"id": third.id, "name": "Third", "email": "third@example.com"},
    ]
    assert page_response.status_code == 200
    assert page_response.json() == [
        {"id": third.id, "name": "Third", "email": "third@example.com"}
    ]


def test_update_user_name_only(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    user = make_user(name="Old", email="keep@example.com")

    response = client.patch(f"/users/{user.id}", json={"name": "New"})

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "name": "New",
        "email": "keep@example.com",
    }


def test_update_user_same_email_allowed(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    user = make_user(name="Old", email="same@example.com")

    response = client.patch(
        f"/users/{user.id}", json={"name": "New", "email": "same@example.com"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "name": "New",
        "email": "same@example.com",
    }


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
    assert response.content == b""
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
