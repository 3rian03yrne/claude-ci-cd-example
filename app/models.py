from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str
    email: str


class User(UserBase, table=True):
    # Emails are unique among active users only, so a soft-deleted user's
    # email can be registered again.
    __table_args__ = (
        Index(
            "ix_user_email_active",
            "email",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    deleted_at: datetime | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    name: str | None = None
    email: str | None = None


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
    deleted_at: datetime | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(SQLModel):
    item: str | None = None
    quantity: int | None = Field(default=None, gt=0)
    total: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    status: str | None = None


class OrderPublic(OrderBase):
    id: int
    created_at: datetime
