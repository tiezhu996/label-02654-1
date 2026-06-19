"""CRUD operations for AuditLog model."""

import json
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction


class AuditLogCRUD:
    """CRUD operations for AuditLog."""

    def create(
        self,
        db: Session,
        action: AuditAction,
        operator_id: int,
        operator_name: str,
        target_type: str = "employee",
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            action=action,
            operator_id=operator_id,
            operator_name=operator_name,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            target_name=target_name,
            changes=json.dumps(changes, ensure_ascii=False, default=str) if changes else None,
            summary=summary,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_list(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        action: Optional[AuditAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Tuple[List[AuditLog], int]:
        """Get paginated list of audit logs with filters."""
        query = db.query(AuditLog)

        if action:
            query = query.filter(AuditLog.action == action)

        if start_time:
            query = query.filter(AuditLog.created_at >= start_time)

        if end_time:
            query = query.filter(AuditLog.created_at <= end_time)

        total = query.count()

        query = query.order_by(AuditLog.created_at.desc())

        offset = (page - 1) * page_size
        logs = query.offset(offset).limit(page_size).all()

        return logs, total

    @staticmethod
    def parse_changes(log: AuditLog) -> Optional[Dict[str, Any]]:
        """Parse JSON-serialized changes back to dict."""
        if not log.changes:
            return None
        try:
            return json.loads(log.changes)
        except (ValueError, TypeError):
            return None


audit_log_crud = AuditLogCRUD()
