from fastapi import APIRouter, HTTPException

from app.database import SessionDep
from app.models import User, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: int, session: SessionDep) -> UserPublic:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# TODO: create user, list users
