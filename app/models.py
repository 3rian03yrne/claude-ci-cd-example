from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str
    email: str


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class UserPublic(UserBase):
    id: int


class OrderBase(SQLModel):
    item: str
    quantity: int = Field(gt=0)
    total: Decimal = Field(max_digits=10, decimal_places=2)
    status: str = "pending"
    user_id: int = Field(foreign_key="user.id")


class Order(OrderBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderPublic(OrderBase):
    id: int
    created_at: datetime
