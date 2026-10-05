"""Registration, login, and current-account endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import TokenResponse, UserLogin, UserRead, UserRegister

router = APIRouter()
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-account-password")


def _invalid_login_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _issue_token(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserRead.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_account(payload: UserRegister, db: DbSession) -> TokenResponse:
    existing_user = await db.scalar(select(User.id).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None
    await db.refresh(user)
    return _issue_token(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: DbSession) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    password_hash = user.hashed_password if user is not None else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(payload.password, password_hash)
    if user is None or not password_matches or not user.is_active:
        raise _invalid_login_error()
    return _issue_token(user)


@router.get("/me", response_model=UserRead)
async def get_current_account(user: CurrentUser) -> User:
    return user
