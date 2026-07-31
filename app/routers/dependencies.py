from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncGenerator

import jwt

from fastapi import (
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal, get_session
from app.core.db_manager import DBManager
from app.core.tokens import tokens

from app.models.users import UserOrm, UserSession

# ==========================
# Pagination
# ==========================


class PaginationParams(BaseModel):
    page: Annotated[int, Query(1, ge=1)] = 1
    per_page: Annotated[int, Query(10, ge=1, le=30)] = 10


PaginationDep = Annotated[PaginationParams, Depends()]


# ==========================
# Database
# ==========================

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_db() -> AsyncGenerator[DBManager, None]:
    async with DBManager() as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]


# ==========================
# JWT
# ==========================


def _extract_access_token(request: Request) -> str:

    header = request.headers.get("authorization")

    if header and header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get(settings.ACCESS_COOKIE_NAME)

    if cookie_token:
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token"
    )


async def get_current_user_from_bearer(
    request: Request,
    session: SessionDep,
) -> UserOrm:

    raw_token = _extract_access_token(request)

    try:
        payload = tokens.decode_token(raw_token, expected_type="access")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload["sub"])

    user = await session.get(UserOrm, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ==========================
# Session Auth
# ==========================


def _get_session_token_hash(
    request: Request,
) -> str:

    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not raw_token:
        raise HTTPException(status_code=401, detail="No session cookie")

    return tokens.hash_session_token(raw_token)


async def _find_session(
    session: SessionDep,
    token_hash: str,
) -> UserSession:

    stmt = select(UserSession).where(UserSession.token_hash == token_hash)

    stored_session = await session.scalar(stmt)

    if not stored_session:
        raise HTTPException(status_code=401, detail="Session not found")

    return stored_session


def _absolute_deadline(
    stored_session: UserSession,
):

    return stored_session.created_at + timedelta(
        days=settings.SESSION_ABSOLUTE_TIMEOUT_DAYS
    )


async def _expire_session(
    session: SessionDep,
    stored_session: UserSession,
    message: str,
):

    await session.delete(stored_session)
    await session.commit()

    raise HTTPException(status_code=401, detail=message)


async def get_current_user_from_session(
    request: Request,
    session: SessionDep,
) -> UserOrm:

    token_hash = _get_session_token_hash(request)

    stored_session = await _find_session(session, token_hash)

    now = datetime.now(timezone.utc)

    if stored_session.expires_at <= now:
        await _expire_session(session, stored_session, "Session expired")

    user = await session.get(UserOrm, stored_session.user_id)

    if not user:
        await _expire_session(session, stored_session, "User not found")

    return user


# ==========================
# Current User
# ==========================


async def get_current_user(
    request: Request,
    session: SessionDep,
) -> UserOrm:

    # JWT

    try:
        return await get_current_user_from_bearer(
            request,
            session,
        )

    except HTTPException:
        pass

    # Session

    try:
        return await get_current_user_from_session(
            request,
            session,
        )

    except HTTPException:
        pass

    raise HTTPException(status_code=401, detail="Not authenticated")


CurrentUserDep = Annotated[UserOrm, Depends(get_current_user)]


# ==========================
# Current User ID
# ==========================


async def get_current_user_id(
    user: CurrentUserDep,
) -> int:

    return user.id


UserIdDep = Annotated[int, Depends(get_current_user_id)]
