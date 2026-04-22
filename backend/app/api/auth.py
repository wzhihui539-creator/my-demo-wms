from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import verify_password, create_access_token, decode_access_token
from app.services import UserService
from app.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user = await UserService.get_by_username(db, data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册（仅管理员可用，简化版）"""
    # 检查用户名是否已存在
    existing = await UserService.get_by_username(db, data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    user = await UserService.create(db, data)
    return user
