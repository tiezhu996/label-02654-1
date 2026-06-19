"""Audit log model for tracking all operations."""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, JSON
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AuditActionType(str, enum.Enum):
    """Audit action type enumeration."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK_UPDATE_STATUS = "bulk_update_status"
    BULK_DELETE = "bulk_delete"
    CSV_IMPORT = "csv_import"


class AuditTargetType(str, enum.Enum):
    """Audit target type enumeration."""
    EMPLOYEE = "employee"


class AuditLog(Base):
    """Audit log model for tracking all data modification operations."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(SQLEnum(AuditActionType), nullable=False, index=True)
    target_type = Column(SQLEnum(AuditTargetType), nullable=False, index=True)
    target_id = Column(String(50), nullable=True, index=True)
    operator_id = Column(Integer, nullable=False, index=True)
    operator_name = Column(String(100), nullable=False)
    action_detail = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
