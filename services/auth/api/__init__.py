"""Auth FastAPI router"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.errors import safe_detail_for_status, safe_error_detail
from services.auth.schemas import TokenRefresh, TokenResponse, UserInfo, UserLogin, UserRegister
from services.auth.service import AuthService

__all__ = [
    'APIRouter',
    'Annotated',
    'AsyncSession',
    'AuthService',
    'Depends',
    'HTTPException',
    'TokenRefresh',
    'TokenResponse',
    'UserInfo',
    'UserLogin',
    'UserRegister',
    'get_db',
    'hub',
    'login',
    'register',
    'router',
    'safe_detail_for_status',
    'safe_error_detail',
]


# Compatibility: get_db via hub
async def get_db():
    async with hub.get_async_session() as session:
        yield session


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserInfo, status_code=201)
async def register(data: UserRegister, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        user = await AuthService(db).register(data)
        return UserInfo(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await AuthService(db).login(data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=safe_detail_for_status(e, 401)) from e
