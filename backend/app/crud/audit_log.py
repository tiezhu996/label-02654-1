"""CRUD operations for AuditLog model."""

from sqlalchemy.orm import Session
from typing import Optional, List, Tuple, Any, Dict
from datetime import datetime

from app.models.audit_log import AuditLog, AuditActionType
from app.models.user import User


class AuditLogCRUD:
    """CRUD operations for AuditLog."""

    def create(
        self,
        db: Session,
        action_type: AuditActionType,
        operator: User,
        target_ids: Optional[List[int]] = None,
        target_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        db_log = AuditLog(
            action_type=action_type,
            operator_id=operator.id,
            operator_name=operator.full_name or operator.username,
            target_ids=target_ids,
            target_name=target_name,
            changes=changes,
            details=details
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    def get_list(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        action_type: Optional[AuditActionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[AuditLog], int]:
        """Get paginated list of audit logs with filters."""
        query = db.query(AuditLog)

        if action_type:
            query = query.filter(AuditLog.action_type == action_type)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        total = query.count()

        query = query.order_by(AuditLog.created_at.desc())

        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()

        return logs, total


audit_log_crud = AuditLogCRUD()
