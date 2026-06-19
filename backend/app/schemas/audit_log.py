"""Audit log schemas for request/response validation."""

from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

from app.models.audit_log import AuditActionType


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    action_type: AuditActionType
    operator_id: int
    operator_name: str
    target_ids: Optional[List[int]] = None
    target_name: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    details: Optional[str] = None
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
