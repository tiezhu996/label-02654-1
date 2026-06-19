"""Employee API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
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
    EmployeeListResponse
)
from app.schemas.audit_log import (
    BulkStatusUpdateRequest,
    BulkDeleteRequest,
    CsvImportResult
)
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.employee import EmployeeStatus
from app.services.employee_service import employee_service

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
    departments = employee_crud.get_all_departments(db)
    return {"departments": departments}


@router.get("/statistics", summary="获取员工统计数据")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    employees, _ = employee_crud.get_list(
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


@router.get("/{employee_id}", response_model=EmployeeResponse, summary="获取员工详情")
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if employee_crud.get_by_email(db, email=employee_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用"
        )

    employee = employee_service.create_employee(
        db, employee_in, current_user, request
    )
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse, summary="更新员工信息")
async def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    employee = employee_crud.get_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )

    if employee_in.email and employee_in.email != employee.email:
        if employee_crud.get_by_email(db, email=employee_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )

    employee = employee_service.update_employee(
        db, employee, employee_in, current_user, request
    )
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除员工")
async def delete_employee(
    employee_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    employee = employee_crud.get_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="员工不存在"
        )

    employee_service.delete_employee(db, employee, current_user, request)
    return None


@router.post("/bulk-status-update", summary="批量修改员工状态(仅管理员)")
async def bulk_update_status(
    body: BulkStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    try:
        target_status = EmployeeStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的状态值，应为active或inactive"
        )

    result = employee_service.bulk_update_status(
        db, body.ids, target_status, current_user, request
    )

    message_parts = [f"成功修改 {result['success_count']} 名员工状态"]
    if result["skipped_inactive"]:
        skipped_names = [f"{s['name']}({s['employee_id']})" for s in result["skipped_inactive"]]
        message_parts.append(f"跳过已离职员工 {len(result['skipped_inactive'])} 名: {', '.join(skipped_names)}")
    if result["not_found_ids"]:
        message_parts.append(f"未找到 {len(result['not_found_ids'])} 条记录")

    return {
        "message": "；".join(message_parts),
        **result
    }


@router.post("/bulk-delete", summary="批量删除员工(仅管理员)")
async def bulk_delete(
    body: BulkDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = employee_service.bulk_delete(
        db, body.ids, current_user, request
    )

    message_parts = [f"成功删除 {result['success_count']} 名员工"]
    if result["not_found_ids"]:
        message_parts.append(f"未找到 {len(result['not_found_ids'])} 条记录")

    return {
        "message": "；".join(message_parts),
        **result
    }


@router.post("/import", response_model=CsvImportResult, summary="CSV导入员工(仅管理员)")
async def import_employees_csv(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传CSV格式文件"
        )

    content = await file.read()
    result = employee_service.import_csv(
        db, content, current_user, request
    )
    return result
