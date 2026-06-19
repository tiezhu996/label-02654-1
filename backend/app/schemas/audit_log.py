"""Audit log schemas for request/response validation."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.audit_log import AuditActionType, AuditTargetType


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    action_type: AuditActionType
    target_type: AuditTargetType
    target_id: Optional[str] = None
    operator_id: int
    operator_name: str
    action_detail: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
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


class BulkStatusUpdateRequest(BaseModel):
    """Schema for bulk status update request."""
    ids: List[int]
    status: str


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    ids: List[int]


class CsvImportRowError(BaseModel):
    """Schema for CSV import row error."""
    row: int
    message: str


class CsvImportResult(BaseModel):
    """Schema for CSV import result."""
    success_count: int
    failed_count: int
    errors: List[CsvImportRowError]
