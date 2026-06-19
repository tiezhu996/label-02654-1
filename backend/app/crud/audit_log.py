"""CRUD operations for AuditLog model."""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from app.models.audit_log import AuditLog, AuditActionType, AuditTargetType
from app.models.user import User


class AuditLogCRUD:
    """CRUD operations for AuditLog."""

    def create(
        self,
        db: Session,
        action_type: AuditActionType,
        target_type: AuditTargetType,
        target_id: Optional[str],
        operator: User,
        action_detail: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry."""
        db_audit = AuditLog(
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            operator_id=operator.id,
            operator_name=operator.full_name or operator.username,
            action_detail=action_detail,
            ip_address=ip_address
        )
        db.add(db_audit)
        db.commit()
        db.refresh(db_audit)
        return db_audit

    def get_list(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        action_type: Optional[AuditActionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        operator_id: Optional[int] = None
    ) -> Tuple[List[AuditLog], int]:
        """Get paginated list of audit logs with filters."""
        query = db.query(AuditLog)

        if action_type:
            query = query.filter(AuditLog.action_type == action_type)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        if operator_id:
            query = query.filter(AuditLog.operator_id == operator_id)

        total = query.count()

        query = query.order_by(AuditLog.created_at.desc())

        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()

        return logs, total


audit_log_crud = AuditLogCRUD()
