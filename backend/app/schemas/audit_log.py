"""Audit log schemas for request/response validation."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    action: AuditAction
    operator_id: int
    operator_name: str
    target_type: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response."""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
