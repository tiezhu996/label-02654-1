"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import user_crud
from app.schemas.user import UserLogin, Token, UserCreate, UserResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录，返回 JWT Token。
    """
    user = user_crud.authenticate(db, username=user_in.username, password=user_in.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    注册新用户。
    """
    # Check if username exists
    if user_crud.get_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # Check if email exists
    if user_crud.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    user = user_crud.create(db, user_in)
    return user


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息。
    """
    return current_user
