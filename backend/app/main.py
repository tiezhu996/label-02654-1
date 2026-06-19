"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, employees
from app.models.user import User, UserRole
from app.crud.user import user_crud
from app.core.database import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("=" * 50)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 50)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    # Create default admin user if not exists
    db = SessionLocal()
    try:
        admin = user_crud.get_by_username(db, "admin")
        if not admin:
            from app.schemas.user import UserCreate
            admin_user = UserCreate(
                username="admin",
                email="admin@example.com",
                password="admin123",
                full_name="系统管理员",
                role=UserRole.ADMIN
            )
            user_crud.create(db, admin_user)
            print("✅ 默认管理员账号创建完成 (admin / admin123)")
        
        # Create default user if not exists
        user = user_crud.get_by_username(db, "user")
        if not user:
            from app.schemas.user import UserCreate
            normal_user = UserCreate(
                username="user",
                email="user@example.com",
                password="user123",
                full_name="普通用户",
                role=UserRole.USER
            )
            user_crud.create(db, normal_user)
            print("✅ 默认普通用户创建完成 (user / user123)")
    finally:
        db.close()
    
    print("=" * 50)
    print("✅ Startup Success")
    print(f"📖 API 文档: http://localhost:8000/docs")
    print(f"📖 ReDoc: http://localhost:8000/redoc")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("👋 应用关闭")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 FastAPI 的员工信息管理系统，支持增删改查、权限管理和数据报表",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(employees.router, prefix="/api")


@app.get("/", tags=["健康检查"])
async def root():
    """Root endpoint for health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
