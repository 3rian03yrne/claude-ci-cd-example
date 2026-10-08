from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models import User


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
