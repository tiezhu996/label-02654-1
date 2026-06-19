"""Employee business service with audit logging."""

from sqlalchemy.orm import Session
from typing import List, Tuple, Optional, Any, Dict
from datetime import date, datetime
from pydantic import ValidationError
import csv
import io
import json

from app.models.user import User
from app.models.employee import Employee, EmployeeStatus, Gender
from app.models.audit_log import AuditActionType
from app.crud.employee import employee_crud
from app.crud.audit_log import audit_log_crud
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    BatchUpdateStatusRequest,
    BatchDeleteRequest,
    BatchOperationResponse,
    BatchOperationError,
    CsvImportResponse,
    CsvImportRowResult
)


class EmployeeService:
    """Employee business service with audit logging."""

    def _to_serializable(self, value: Any) -> Any:
        """Convert a value to a JSON-serializable type."""
        if value is None:
            return None
        if isinstance(value, (Gender, EmployeeStatus)):
            return value.value
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    def _get_field_changes(self, old: Employee, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare old employee with new data and return changes."""
        changes: Dict[str, Any] = {}
        field_labels = {
            "name": "姓名",
            "gender": "性别",
            "age": "年龄",
            "department": "部门",
            "position": "职位",
            "email": "邮箱",
            "phone": "电话",
            "hire_date": "入职日期",
            "status": "状态"
        }

        for field, new_value in new_data.items():
            if field not in field_labels:
                continue
            old_value = getattr(old, field)
            old_value = self._to_serializable(old_value)
            new_value = self._to_serializable(new_value)
            if str(old_value) != str(new_value):
                changes[field_labels.get(field, field)] = {
                    "old": old_value,
                    "new": new_value
                }
        return changes

    def _parse_gender(self, value: str) -> Gender:
        """Parse gender from Chinese or English string."""
        gender_map = {
            "男": Gender.MALE,
            "女": Gender.FEMALE,
            "male": Gender.MALE,
            "female": Gender.FEMALE
        }
        return gender_map.get(value.strip(), Gender.MALE)

    def _parse_status(self, value: str) -> EmployeeStatus:
        """Parse status from Chinese or English string."""
        status_map = {
            "在职": EmployeeStatus.ACTIVE,
            "离职": EmployeeStatus.INACTIVE,
            "active": EmployeeStatus.ACTIVE,
            "inactive": EmployeeStatus.INACTIVE
        }
        return status_map.get(value.strip(), EmployeeStatus.ACTIVE)

    def _parse_date(self, value: str) -> date:
        """Parse date from string."""
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()

    def get_by_id(self, db: Session, employee_id: int) -> Optional[Employee]:
        """Get employee by ID."""
        return employee_crud.get_by_id(db, employee_id)

    def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
        """Get employee by email."""
        return employee_crud.get_by_email(db, email)

    def get_list(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[EmployeeStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Employee], int]:
        """Get paginated list of employees."""
        return employee_crud.get_list(
            db, page, page_size, search, department, status, sort_by, sort_order
        )

    def get_all_departments(self, db: Session) -> List[str]:
        """Get all unique departments."""
        return employee_crud.get_all_departments(db)

    def get_statistics(self, db: Session) -> dict:
        """Get employee statistics."""
        return employee_crud.get_statistics(db)

    def create(self, db: Session, employee_in: EmployeeCreate, operator: User) -> Employee:
        """Create a new employee with audit logging."""
        employee = employee_crud.create(db, employee_in)

        changes: Dict[str, Any] = {}
        field_labels = {
            "employee_id": "工号",
            "name": "姓名",
            "gender": "性别",
            "age": "年龄",
            "department": "部门",
            "position": "职位",
            "email": "邮箱",
            "phone": "电话",
            "hire_date": "入职日期",
            "status": "状态"
        }
        data = employee_in.model_dump()
        for field, value in data.items():
            if field in field_labels:
                changes[field_labels[field]] = {"old": None, "new": self._to_serializable(value)}
        changes[field_labels["employee_id"]] = {"old": None, "new": self._to_serializable(employee.employee_id)}

        audit_log_crud.create(
            db,
            action_type=AuditActionType.CREATE,
            operator=operator,
            target_ids=[employee.id],
            target_name=employee.name,
            changes=changes,
            details=f"创建员工: {employee.name} ({employee.employee_id})"
        )

        return employee

    def update(
        self,
        db: Session,
        employee: Employee,
        employee_in: EmployeeUpdate,
        operator: User
    ) -> Employee:
        """Update an employee with audit logging."""
        update_data = employee_in.model_dump(exclude_unset=True)
        changes = self._get_field_changes(employee, update_data)

        updated_employee = employee_crud.update(db, employee, employee_in)

        if changes:
            audit_log_crud.create(
                db,
                action_type=AuditActionType.UPDATE,
                operator=operator,
                target_ids=[employee.id],
                target_name=employee.name,
                changes=changes,
                details=f"更新员工: {employee.name} ({employee.employee_id})"
            )

        return updated_employee

    def delete(self, db: Session, employee: Employee, operator: User) -> None:
        """Delete an employee with audit logging."""
        emp_name = employee.name
        emp_id = employee.employee_id
        emp_pk = employee.id

        field_labels = {
            "employee_id": "工号",
            "name": "姓名",
            "department": "部门",
            "position": "职位",
            "email": "邮箱",
            "status": "状态"
        }
        changes: Dict[str, Any] = {}
        for field, label in field_labels.items():
            val = getattr(employee, field)
            changes[label] = {"old": self._to_serializable(val), "new": None}

        employee_crud.delete(db, employee)

        audit_log_crud.create(
            db,
            action_type=AuditActionType.DELETE,
            operator=operator,
            target_ids=[emp_pk],
            target_name=emp_name,
            changes=changes,
            details=f"删除员工: {emp_name} ({emp_id})"
        )

    def batch_update_status(
        self,
        db: Session,
        request: BatchUpdateStatusRequest,
        operator: User
    ) -> BatchOperationResponse:
        """Batch update employee status with audit logging. Does not allow changing status for already inactive employees."""
        success_count = 0
        failed_count = 0
        errors: List[BatchOperationError] = []
        succeeded_ids: List[int] = []
        target_names: List[str] = []

        for emp_id in request.ids:
            employee = employee_crud.get_by_id(db, emp_id)
            if not employee:
                failed_count += 1
                errors.append(BatchOperationError(id=emp_id, message="员工不存在"))
                continue

            if employee.status == EmployeeStatus.INACTIVE and request.status != EmployeeStatus.INACTIVE:
                failed_count += 1
                errors.append(BatchOperationError(
                    id=emp_id,
                    message=f"员工 {employee.name} 已是离职状态，不允许变更状态"
                ))
                continue

            if employee.status == request.status:
                failed_count += 1
                errors.append(BatchOperationError(
                    id=emp_id,
                    message=f"员工 {employee.name} 已是{('在职' if request.status == EmployeeStatus.ACTIVE else '离职')}状态"
                ))
                continue

            old_status = employee.status
            employee_crud.update(
                db,
                employee,
                EmployeeUpdate(status=request.status)
            )
            success_count += 1
            succeeded_ids.append(emp_id)
            target_names.append(employee.name)

        if succeeded_ids:
            status_label = "在职" if request.status == EmployeeStatus.ACTIVE else "离职"
            audit_log_crud.create(
                db,
                action_type=AuditActionType.BATCH_UPDATE_STATUS,
                operator=operator,
                target_ids=succeeded_ids,
                changes={
                    "状态": {
                        "old": "多个值",
                        "new": status_label
                    }
                },
                details=f"批量修改 {len(succeeded_ids)} 名员工状态为{status_label}: {', '.join(target_names[:5])}{'...' if len(target_names) > 5 else ''}"
            )

        return BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )

    def batch_delete(
        self,
        db: Session,
        request: BatchDeleteRequest,
        operator: User
    ) -> BatchOperationResponse:
        """Batch delete employees with audit logging."""
        success_count = 0
        failed_count = 0
        errors: List[BatchOperationError] = []
        succeeded_ids: List[int] = []
        target_names: List[str] = []
        all_changes: Dict[str, Any] = {}

        for emp_id in request.ids:
            employee = employee_crud.get_by_id(db, emp_id)
            if not employee:
                failed_count += 1
                errors.append(BatchOperationError(id=emp_id, message="员工不存在"))
                continue

            emp_name = employee.name
            emp_pk = employee.id
            succeeded_ids.append(emp_pk)
            target_names.append(emp_name)

            employee_crud.delete(db, employee)
            success_count += 1

        if succeeded_ids:
            audit_log_crud.create(
                db,
                action_type=AuditActionType.BATCH_DELETE,
                operator=operator,
                target_ids=succeeded_ids,
                details=f"批量删除 {len(succeeded_ids)} 名员工: {', '.join(target_names[:5])}{'...' if len(target_names) > 5 else ''}"
            )

        return BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors
        )

    def import_csv(
        self,
        db: Session,
        file_content: bytes,
        operator: User
    ) -> CsvImportResponse:
        """Import employees from CSV file."""
        results: List[CsvImportRowResult] = []
        success_count = 0
        failed_count = 0

        try:
            content_str = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            content_str = file_content.decode("gbk")

        reader = csv.reader(io.StringIO(content_str))
        rows = list(reader)

        if len(rows) < 2:
            return CsvImportResponse(
                success_count=0,
                failed_count=0,
                total_count=0,
                results=[]
            )

        for row_idx, row in enumerate(rows[1:], start=2):
            if len(row) < 10:
                failed_count += 1
                results.append(CsvImportRowResult(
                    row=row_idx,
                    success=False,
                    message="列数不足，需要10列数据"
                ))
                continue

            try:
                employee_id = row[0].strip()
                name = row[1].strip()
                gender_str = row[2].strip()
                age_str = row[3].strip()
                department = row[4].strip()
                position = row[5].strip()
                email = row[6].strip()
                phone = row[7].strip()
                hire_date_str = row[8].strip()
                status_str = row[9].strip()

                if not name:
                    raise ValueError("姓名不能为空")
                if not email:
                    raise ValueError("邮箱不能为空")
                if not department:
                    raise ValueError("部门不能为空")
                if not position:
                    raise ValueError("职位不能为空")
                if not hire_date_str:
                    raise ValueError("入职日期不能为空")

                try:
                    age = int(age_str)
                except ValueError:
                    raise ValueError(f"年龄格式错误: {age_str}")

                if age <= 0 or age > 150:
                    raise ValueError(f"年龄不合法: {age}")

                try:
                    gender = self._parse_gender(gender_str)
                except Exception:
                    raise ValueError(f"性别格式错误: {gender_str}")

                try:
                    hire_date = self._parse_date(hire_date_str)
                except ValueError:
                    raise ValueError(f"入职日期格式错误，应为 YYYY-MM-DD: {hire_date_str}")

                try:
                    status = self._parse_status(status_str) if status_str else EmployeeStatus.ACTIVE
                except Exception:
                    raise ValueError(f"状态格式错误: {status_str}")

                existing_email = employee_crud.get_by_email(db, email)
                if existing_email:
                    raise ValueError(f"邮箱已存在: {email}")

                if employee_id:
                    existing_emp_id = employee_crud.get_by_employee_id(db, employee_id)
                    if existing_emp_id:
                        raise ValueError(f"工号已存在: {employee_id}")

                from app.schemas.employee import EmployeeCreate
                try:
                    employee_in = EmployeeCreate(
                        name=name,
                        gender=gender,
                        age=age,
                        department=department,
                        position=position,
                        email=email,
                        phone=phone if phone else None,
                        hire_date=hire_date,
                        status=status
                    )
                except ValidationError as ve:
                    error_messages = []
                    for err in ve.errors():
                        field = err.get('loc', ('',))[0] if err.get('loc') else ''
                        error_messages.append(f"{field}: {err.get('msg', '')}")
                    raise ValueError("; ".join(error_messages))

                db_employee = Employee(
                    employee_id=employee_id if employee_id else employee_crud._generate_employee_id(),
                    **employee_in.model_dump()
                )
                db.add(db_employee)
                db.commit()
                db.refresh(db_employee)

                audit_log_crud.create(
                    db,
                    action_type=AuditActionType.CREATE,
                    operator=operator,
                    target_ids=[db_employee.id],
                    target_name=db_employee.name,
                    details=f"CSV导入创建员工: {db_employee.name} ({db_employee.employee_id})"
                )

                success_count += 1
                results.append(CsvImportRowResult(
                    row=row_idx,
                    success=True,
                    employee_id=db_employee.employee_id
                ))

            except ValueError as e:
                db.rollback()
                failed_count += 1
                results.append(CsvImportRowResult(
                    row=row_idx,
                    success=False,
                    message=str(e)
                ))
            except Exception as e:
                db.rollback()
                failed_count += 1
                results.append(CsvImportRowResult(
                    row=row_idx,
                    success=False,
                    message=f"导入失败: {str(e)}"
                ))

        if success_count > 0:
            audit_log_crud.create(
                db,
                action_type=AuditActionType.IMPORT,
                operator=operator,
                details=f"CSV导入完成: 成功 {success_count} 条，失败 {failed_count} 条"
            )

        return CsvImportResponse(
            success_count=success_count,
            failed_count=failed_count,
            total_count=len(rows) - 1,
            results=results
        )


employee_service = EmployeeService()
