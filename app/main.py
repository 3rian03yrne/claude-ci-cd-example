from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers import orders, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="Claude CI/CD Example", lifespan=lifespan)

app.include_router(users.router)
app.include_router(orders.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello World"}
