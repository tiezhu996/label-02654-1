"""Employee schemas for request/response validation."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

from app.models.employee import Gender, EmployeeStatus


class EmployeeBase(BaseModel):
    """Base employee schema."""
    name: str
    gender: Gender
    age: int
    department: str
    position: str
    email: EmailStr
    phone: Optional[str] = None
    hire_date: date
    status: EmployeeStatus = EmployeeStatus.ACTIVE


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee."""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""
    name: Optional[str] = None
    gender: Optional[Gender] = None
    age: Optional[int] = None
    department: Optional[str] = None
    position: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hire_date: Optional[date] = None
    status: Optional[EmployeeStatus] = None


class EmployeeResponse(EmployeeBase):
    """Schema for employee response."""
    id: int
    employee_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """Schema for paginated employee list response."""
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkUpdateStatusRequest(BaseModel):
    """Schema for bulk updating employee status."""
    ids: List[int]
    status: EmployeeStatus


class BulkDeleteRequest(BaseModel):
    """Schema for bulk deleting employees."""
    ids: List[int]


class BulkOperationResult(BaseModel):
    """Schema for bulk operation result."""
    success_count: int
    failed_count: int
    failed_items: List[dict] = []  # [{id, reason}]


class CsvImportRowError(BaseModel):
    """Schema describing a failed row during CSV import."""
    row: int
    reason: str


class CsvImportResult(BaseModel):
    """Schema for CSV import result."""
    success_count: int
    failed_count: int
    errors: List[CsvImportRowError] = []
