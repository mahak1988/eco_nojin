"""Auth FastAPI router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from services.auth.schemas import TokenRefresh, TokenResponse, UserInfo, UserLogin, UserRegister
from services.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserInfo, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService(db).register(data)
        return UserInfo(
            id=user.id, email=user.email, username=user.username,
            is_active=user.is_active, is_verified=user.is_verified,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService(db).login(data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
