"""Audit log API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.crud.audit_log import audit_log_crud
from app.schemas.audit_log import AuditLogListResponse
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.audit_log import AuditActionType

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


@router.get("", response_model=AuditLogListResponse, summary="获取审计日志列表")
async def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    action_type: Optional[AuditActionType] = Query(None, description="操作类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    获取审计日志列表，支持按操作类型和时间范围筛选（仅管理员）。
    """
    logs, total = audit_log_crud.get_list(
        db,
        page=page,
        page_size=page_size,
        action_type=action_type,
        start_date=start_date,
        end_date=end_date
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
