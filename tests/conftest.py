import os

# Must be set before the app is imported: app.database builds its engine at
# import time, and this keeps tests from ever pointing it at ./app.db.
os.environ["DATABASE_URL"] = "sqlite://"

from collections.abc import Callable, Iterator
from decimal import Decimal
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models import Order, User


@pytest.fixture
def engine() -> Iterator[Engine]:
    # Fresh in-memory DB per test; StaticPool keeps one connection so every
    # session sees the same database.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    # Used by the factories to arrange test data. Requests get their own
    # session (see `client`), so endpoints read from the DB, not this
    # session's identity map.
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    def get_session_override() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    try:
        # Not used as a context manager, so the lifespan (which creates tables
        # on the app's own engine) doesn't run.
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def make_user(session: Session) -> Callable[..., User]:
    ids = count(1)

    def _make_user(name: str | None = None, email: str | None = None) -> User:
        n = next(ids)
        user = User(name=name or f"User {n}", email=email or f"user{n}@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def make_order(
    session: Session, make_user: Callable[..., User]
) -> Callable[..., Order]:
    def _make_order(
        user: User | None = None,
        item: str = "Widget",
        quantity: int = 2,
        total: Decimal = Decimal("12.50"),
    ) -> Order:
        user = user or make_user()
        order = Order(item=item, quantity=quantity, total=total, user_id=user.id)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order

    return _make_order
