"""Employee API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io

from app.core.database import get_db
from app.crud.employee import employee_crud
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    BulkUpdateStatusRequest,
    BulkDeleteRequest,
    BulkOperationResult,
    CsvImportResult,
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
    """
    获取员工列表，支持分页、搜索、筛选和排序。
    """
    employees, total = employee_crud.get_list(
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
    """
    获取所有部门列表（用于筛选下拉框）。
    """
    departments = employee_crud.get_all_departments(db)
    return {"departments": departments}


@router.get("/statistics", summary="获取员工统计数据")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取员工统计数据（用于Dashboard图表）。
    """
    stats = employee_crud.get_statistics(db)
    return stats


@router.get("/export", summary="导出员工数据(CSV)")
async def export_employees(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[EmployeeStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出员工数据为CSV格式。
    """
    employees, _ = employee_crud.get_list(
        db,
        page=1,
        page_size=10000,  # Export all
        search=search,
        department=department,
        status=status
    )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "工号", "姓名", "性别", "年龄", "部门", "职位", 
        "邮箱", "电话", "入职日期", "状态"
    ])
    
    # Write data
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


@router.post(
    "/import",
    response_model=CsvImportResult,
    summary="CSV 导入员工(仅管理员)",
)
async def import_employees(
    file: UploadFile = File(..., description="CSV 文件,格式与导出 CSV 一致"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    通过 CSV 批量导入员工(仅管理员)。
    - 文件格式与导出 CSV 一致(中文表头);
    - 逐行独立校验邮箱唯一性和必填字段;
    - 任意行失败不阻断整批操作;
    - 返回成功条数和每行失败原因。
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传 .csv 文件",
        )
    csv_bytes = await file.read()
    if not csv_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件为空",
        )
    return employee_crud.import_from_csv(db, csv_bytes=csv_bytes, operator=current_user)


@router.post(
    "/bulk-status",
    response_model=BulkOperationResult,
    summary="批量修改员工状态(仅管理员)",
)
async def bulk_update_status(
    payload: BulkUpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    批量修改员工状态(仅管理员)。已离职员工不允许通过批量操作变更状态。
    """
    if not payload.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要操作的员工",
        )
    return employee_crud.bulk_update_status(
        db,
        ids=payload.ids,
        new_status=payload.status,
        operator=current_user,
    )


@router.post(
    "/bulk-delete",
    response_model=BulkOperationResult,
    summary="批量删除员工(仅管理员)",
)
async def bulk_delete(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    批量删除员工(仅管理员)。
    """
    if not payload.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要删除的员工",
        )
    return employee_crud.bulk_delete(
        db,
        ids=payload.ids,
        operator=current_user,
    )


@router.get("/{employee_id}", response_model=EmployeeResponse, summary="获取员工详情")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取员工详情。
    """
    employee = employee_crud.get_by_id(db, employee_id)
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
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    创建新员工（仅管理员）。
    """
    # Check if email exists
    if employee_crud.get_by_email(db, email=employee_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用"
        )
    
    employee = employee_crud.create(db, employee_in, operator=current_user)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse, summary="更新员工信息")
async def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    更新员工信息（仅管理员）。
    """
    employee = employee_crud.get_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    # Check email uniqueness if updating email
    if employee_in.email and employee_in.email != employee.email:
        if employee_crud.get_by_email(db, email=employee_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    employee = employee_crud.update(db, employee, employee_in, operator=current_user)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除员工")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    删除员工（仅管理员）。
    """
    employee = employee_crud.get_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )
    
    employee_crud.delete(db, employee, operator=current_user)
    return None
