"""Employee business service layer with audit logging."""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple, BinaryIO
from datetime import date, datetime
import csv
import io

from app.models.user import User
from app.models.employee import Employee, EmployeeStatus, Gender
from app.models.audit_log import AuditActionType, AuditTargetType
from app.crud.employee import employee_crud
from app.crud.audit_log import audit_log_crud
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


GENDER_MAP_ZH = {"男": "male", "女": "female"}
STATUS_MAP_ZH = {"在职": "active", "离职": "inactive"}
REQUIRED_FIELDS = ["姓名", "性别", "年龄", "部门", "职位", "邮箱", "入职日期"]


class EmployeeService:
    """Business service for employee operations with audit logging."""

    def _get_client_ip(self, request: Any = None) -> Optional[str]:
        """Extract client IP from request if available."""
        if request is None:
            return None
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = getattr(request, "client", None)
        if client is not None and hasattr(client, "host"):
            return client.host
        return None

    def create_employee(
        self,
        db: Session,
        employee_in: EmployeeCreate,
        operator: User,
        request: Any = None
    ) -> Employee:
        """Create a new employee with audit log."""
        employee = employee_crud.create(db, employee_in)

        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.CREATE,
            target_type=AuditTargetType.EMPLOYEE,
            target_id=str(employee.id),
            operator=operator,
            action_detail={
                "employee_id": employee.employee_id,
                "name": employee.name,
                "changes": {
                    "after": {
                        "name": employee.name,
                        "email": employee.email,
                        "department": employee.department,
                        "position": employee.position,
                        "status": employee.status.value
                    }
                }
            },
            ip_address=self._get_client_ip(request)
        )

        return employee

    def update_employee(
        self,
        db: Session,
        employee: Employee,
        employee_in: EmployeeUpdate,
        operator: User,
        request: Any = None
    ) -> Employee:
        """Update an employee with audit log."""
        before_data = {
            "name": employee.name,
            "gender": employee.gender.value,
            "age": employee.age,
            "department": employee.department,
            "position": employee.position,
            "email": employee.email,
            "phone": employee.phone,
            "hire_date": employee.hire_date.isoformat() if employee.hire_date else None,
            "status": employee.status.value
        }

        updated_employee = employee_crud.update(db, employee, employee_in)

        update_data = employee_in.model_dump(exclude_unset=True)
        after_data = {
            "name": updated_employee.name,
            "gender": updated_employee.gender.value,
            "age": updated_employee.age,
            "department": updated_employee.department,
            "position": updated_employee.position,
            "email": updated_employee.email,
            "phone": updated_employee.phone,
            "hire_date": updated_employee.hire_date.isoformat() if updated_employee.hire_date else None,
            "status": updated_employee.status.value
        }

        changes = {}
        for field, new_value in update_data.items():
            old_value = before_data.get(field)
            if field == "hire_date" and isinstance(new_value, date):
                new_value = new_value.isoformat()
            if old_value != new_value:
                changes[field] = {"old": old_value, "new": new_value}

        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.UPDATE,
            target_type=AuditTargetType.EMPLOYEE,
            target_id=str(updated_employee.id),
            operator=operator,
            action_detail={
                "employee_id": updated_employee.employee_id,
                "name": updated_employee.name,
                "changes": changes
            },
            ip_address=self._get_client_ip(request)
        )

        return updated_employee

    def delete_employee(
        self,
        db: Session,
        employee: Employee,
        operator: User,
        request: Any = None
    ) -> None:
        """Delete an employee with audit log."""
        employee_data = {
            "employee_id": employee.employee_id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "position": employee.position,
            "status": employee.status.value
        }

        employee_crud.delete(db, employee)

        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.DELETE,
            target_type=AuditTargetType.EMPLOYEE,
            target_id=str(employee.id),
            operator=operator,
            action_detail=employee_data,
            ip_address=self._get_client_ip(request)
        )

    def bulk_update_status(
        self,
        db: Session,
        ids: List[int],
        target_status: EmployeeStatus,
        operator: User,
        request: Any = None
    ) -> Dict[str, Any]:
        """Bulk update employee status. Inactive employees cannot be changed via bulk operation."""
        success_ids: List[int] = []
        skipped_inactive: List[Dict[str, Any]] = []
        not_found_ids: List[int] = []

        employees = db.query(Employee).filter(Employee.id.in_(ids)).all()
        found_map = {emp.id: emp for emp in employees}

        for emp_id in ids:
            emp = found_map.get(emp_id)
            if not emp:
                not_found_ids.append(emp_id)
                continue

            if emp.status == EmployeeStatus.INACTIVE:
                skipped_inactive.append({
                    "id": emp.id,
                    "employee_id": emp.employee_id,
                    "name": emp.name
                })
                continue

            old_status = emp.status.value
            emp.status = target_status
            success_ids.append(emp.id)

        db.commit()

        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.BULK_UPDATE_STATUS,
            target_type=AuditTargetType.EMPLOYEE,
            target_id=",".join(str(i) for i in success_ids) if success_ids else None,
            operator=operator,
            action_detail={
                "target_status": target_status.value,
                "success_count": len(success_ids),
                "success_ids": success_ids,
                "skipped_inactive": skipped_inactive,
                "not_found_ids": not_found_ids
            },
            ip_address=self._get_client_ip(request)
        )

        return {
            "success_count": len(success_ids),
            "skipped_inactive": skipped_inactive,
            "not_found_ids": not_found_ids
        }

    def bulk_delete(
        self,
        db: Session,
        ids: List[int],
        operator: User,
        request: Any = None
    ) -> Dict[str, Any]:
        """Bulk delete employees."""
        success_ids: List[int] = []
        deleted_details: List[Dict[str, Any]] = []
        not_found_ids: List[int] = []

        employees = db.query(Employee).filter(Employee.id.in_(ids)).all()
        found_map = {emp.id: emp for emp in employees}

        for emp_id in ids:
            emp = found_map.get(emp_id)
            if not emp:
                not_found_ids.append(emp_id)
                continue

            deleted_details.append({
                "id": emp.id,
                "employee_id": emp.employee_id,
                "name": emp.name,
                "email": emp.email,
                "department": emp.department
            })
            db.delete(emp)
            success_ids.append(emp.id)

        db.commit()

        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.BULK_DELETE,
            target_type=AuditTargetType.EMPLOYEE,
            target_id=",".join(str(i) for i in success_ids) if success_ids else None,
            operator=operator,
            action_detail={
                "success_count": len(success_ids),
                "success_ids": success_ids,
                "deleted_employees": deleted_details,
                "not_found_ids": not_found_ids
            },
            ip_address=self._get_client_ip(request)
        )

        return {
            "success_count": len(success_ids),
            "not_found_ids": not_found_ids
        }

    def import_csv(
        self,
        db: Session,
        file_content: bytes,
        operator: User,
        request: Any = None
    ) -> Dict[str, Any]:
        """Import employees from CSV file. Rows are validated independently; failures don't block batch."""
        success_count: int = 0
        errors: List[Dict[str, Any]] = []
        successful_employees: List[Dict[str, Any]] = []

        try:
            content = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                content = file_content.decode("gbk")
            except UnicodeDecodeError:
                return {
                    "success_count": 0,
                    "failed_count": 1,
                    "errors": [{"row": 0, "message": "文件编码不支持，请使用UTF-8或GBK编码"}]
                }

        reader = csv.DictReader(io.StringIO(content))
        fieldnames = reader.fieldnames or []

        required_headers = ["工号", "姓名", "性别", "年龄", "部门", "职位", "邮箱", "电话", "入职日期", "状态"]
        missing_headers = [h for h in required_headers if h not in fieldnames]
        if missing_headers:
            return {
                "success_count": 0,
                "failed_count": 1,
                "errors": [{"row": 0, "message": f"CSV缺少必要列: {', '.join(missing_headers)}"}]
            }

        for row_idx, row in enumerate(reader, start=2):
            row_errors: List[str] = []

            name = (row.get("姓名") or "").strip()
            gender_zh = (row.get("性别") or "").strip()
            age_str = (row.get("年龄") or "").strip()
            department = (row.get("部门") or "").strip()
            position = (row.get("职位") or "").strip()
            email = (row.get("邮箱") or "").strip()
            phone = (row.get("电话") or "").strip() or None
            hire_date_str = (row.get("入职日期") or "").strip()
            status_zh = (row.get("状态") or "").strip()

            if not name:
                row_errors.append("姓名不能为空")
            if not department:
                row_errors.append("部门不能为空")
            if not position:
                row_errors.append("职位不能为空")
            if not email:
                row_errors.append("邮箱不能为空")
            if not hire_date_str:
                row_errors.append("入职日期不能为空")

            gender: Optional[Gender] = None
            if gender_zh:
                gender_val = GENDER_MAP_ZH.get(gender_zh)
                if not gender_val:
                    row_errors.append(f"性别值无效: {gender_zh}，应为男或女")
                else:
                    gender = Gender(gender_val)
            else:
                row_errors.append("性别不能为空")

            age: Optional[int] = None
            if age_str:
                try:
                    age = int(age_str)
                    if age < 16 or age > 100:
                        row_errors.append(f"年龄应在16-100之间: {age_str}")
                except ValueError:
                    row_errors.append(f"年龄格式无效: {age_str}")
            else:
                row_errors.append("年龄不能为空")

            hire_date: Optional[date] = None
            if hire_date_str:
                try:
                    hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
                except ValueError:
                    try:
                        hire_date = datetime.strptime(hire_date_str, "%Y/%m/%d").date()
                    except ValueError:
                        row_errors.append(f"入职日期格式无效: {hire_date_str}，应为YYYY-MM-DD")

            status_val = "active"
            if status_zh:
                s = STATUS_MAP_ZH.get(status_zh)
                if not s:
                    row_errors.append(f"状态值无效: {status_zh}，应为在职或离职")
                else:
                    status_val = s

            if email and not row_errors:
                existing = employee_crud.get_by_email(db, email=email)
                if existing:
                    row_errors.append(f"邮箱已存在: {email}")

            if row_errors:
                errors.append({"row": row_idx, "message": "; ".join(row_errors)})
                continue

            try:
                from pydantic import EmailStr
                employee_in = EmployeeCreate(
                    name=name,
                    gender=gender,
                    age=age,
                    department=department,
                    position=position,
                    email=email,
                    phone=phone,
                    hire_date=hire_date,
                    status=EmployeeStatus(status_val)
                )
                new_emp = employee_crud.create(db, employee_in)
                success_count += 1
                successful_employees.append({
                    "id": new_emp.id,
                    "employee_id": new_emp.employee_id,
                    "name": new_emp.name,
                    "email": new_emp.email
                })
            except Exception as e:
                errors.append({"row": row_idx, "message": f"创建失败: {str(e)}"})

        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.CSV_IMPORT,
            target_type=AuditTargetType.EMPLOYEE,
            target_id=None,
            operator=operator,
            action_detail={
                "success_count": success_count,
                "failed_count": len(errors),
                "successful_employees": successful_employees,
                "errors": errors
            },
            ip_address=self._get_client_ip(request)
        )

        return {
            "success_count": success_count,
            "failed_count": len(errors),
            "errors": errors
        }


employee_service = EmployeeService()
