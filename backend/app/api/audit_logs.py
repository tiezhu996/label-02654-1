"""Audit log API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.audit_log import audit_log_crud
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.audit_log import AuditAction

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


@router.get("", response_model=AuditLogListResponse, summary="获取审计日志列表(仅管理员)")
async def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    action: Optional[AuditAction] = Query(None, description="按操作类型筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间(含)"),
    end_time: Optional[datetime] = Query(None, description="结束时间(含)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> AuditLogListResponse:
    """
    获取审计日志列表(仅管理员)，支持按操作类型与时间范围筛选。
    """
    logs, total = audit_log_crud.get_list(
        db,
        page=page,
        page_size=page_size,
        action=action,
        start_time=start_time,
        end_time=end_time,
    )

    items = []
    for log in logs:
        items.append(
            AuditLogResponse(
                id=log.id,
                action=log.action,
                operator_id=log.operator_id,
                operator_name=log.operator_name,
                target_type=log.target_type,
                target_id=log.target_id,
                target_name=log.target_name,
                changes=audit_log_crud.parse_changes(log),
                summary=log.summary,
                created_at=log.created_at,
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
