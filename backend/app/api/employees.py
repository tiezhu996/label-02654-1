"""Employee API endpoints - thin API layer, delegates business logic to service layer."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io

from app.core.database import get_db
from app.services.employee import employee_service
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    BatchUpdateStatusRequest,
    BatchDeleteRequest,
    BatchOperationResponse,
    CsvImportResponse
)
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.employee import EmployeeStatus

router = APIRouter(prefix="/employees", tags=["员工管理"])


@router.get("", response_model=EmployeeListResponse, summary="获取员工列表")
async def get_employees(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词(姓名/工号/部门)"),
    department: Optional[str] = Query(None, description="部门筛选"),
    status: Optional[EmployeeStatus] = Query(None, description="状态筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向(asc/desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated employee list."""
    employees, total = employee_service.get_employees(
        db,
        page=page,
        page_size=page_size,
        search=search,
        department=department,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return EmployeeListResponse(
        items=employees,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/departments", summary="获取所有部门列表")
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all unique departments."""
    departments = employee_service.get_all_departments(db)
    return {"departments": departments}


@router.get("/statistics", summary="获取员工统计数据")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee statistics for dashboard."""
    stats = employee_service.get_statistics(db)
    return stats


@router.get("/export", summary="导出员工数据(CSV)")
async def export_employees(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[EmployeeStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export employees to CSV format."""
    employees, _ = employee_service.get_employees(
        db,
        page=1,
        page_size=10000,
        search=search,
        department=department,
        status=status
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "工号", "姓名", "性别", "年龄", "部门", "职位",
        "邮箱", "电话", "入职日期", "状态"
    ])
    
    gender_map = {"male": "男", "female": "女"}
    status_map = {"active": "在职", "inactive": "离职"}
    
    for emp in employees:
        writer.writerow([
            emp.employee_id,
            emp.name,
            gender_map.get(emp.gender.value, emp.gender.value),
            emp.age,
            emp.department,
            emp.position,
            emp.email,
            emp.phone or "",
            emp.hire_date.strftime("%Y-%m-%d"),
            status_map.get(emp.status.value, emp.status.value)
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )


@router.post("/import", response_model=CsvImportResponse, summary="导入员工数据(CSV)")
async def import_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Import employees from CSV file (admin only)."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传CSV格式文件"
        )
    
    content = await file.read()
    try:
        file_content = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            file_content = content.decode('gbk')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件编码不支持，请使用UTF-8或GBK编码"
            )
    
    result = employee_service.import_csv(db, file_content, current_user)
    return result


@router.post("/batch/status", response_model=BatchOperationResponse, summary="批量更新员工状态")
async def batch_update_status(
    request: BatchUpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Batch update employee status (admin only), inactive employees are skipped."""
    success_count, failed_items = employee_service.batch_update_status(
        db, request.ids, request.status, current_user
    )
    return BatchOperationResponse(
        success_count=success_count,
        failed_items=failed_items
    )


@router.post("/batch/delete", response_model=BatchOperationResponse, summary="批量删除员工")
async def batch_delete(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Batch delete employees (admin only)."""
    success_count, failed_items = employee_service.batch_delete(
        db, request.ids, current_user
    )
    return BatchOperationResponse(
        success_count=success_count,
        failed_items=failed_items
    )


@router.get("/{employee_id}", response_model=EmployeeResponse, summary="获取员工详情")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee details by ID."""
    employee = employee_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    return employee


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, summary="创建员工")
async def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create new employee (admin only)."""
    if employee_service.get_employee_by_email(db, email=employee_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用"
        )
    
    employee = employee_service.create_employee(db, employee_in, current_user)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse, summary="更新员工信息")
async def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update employee information (admin only)."""
    employee = employee_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    if employee_in.email and employee_in.email != employee.email:
        if employee_service.get_employee_by_email(db, email=employee_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    employee = employee_service.update_employee(db, employee, employee_in, current_user)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除员工")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete employee (admin only)."""
    employee = employee_service.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    employee_service.delete_employee(db, employee, current_user)
    return None
