"""Audit log model for tracking all employee operations."""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, JSON, Text
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AuditActionType(str, enum.Enum):
    """Audit action type enumeration."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_UPDATE_STATUS = "batch_update_status"
    BATCH_DELETE = "batch_delete"
    IMPORT = "import"


class AuditLog(Base):
    """Audit log model for tracking all employee operations."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(SQLEnum(AuditActionType), nullable=False, index=True)
    operator_id = Column(Integer, nullable=False, index=True)
    operator_name = Column(String(100), nullable=False)
    target_ids = Column(JSON, nullable=True)
    target_name = Column(String(100), nullable=True)
    changes = Column(JSON, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
