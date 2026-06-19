"""Service layer for employee business logic."""

from sqlalchemy.orm import Session
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, date
import enum

from app.models.employee import Employee, Gender, EmployeeStatus
from app.models.user import User
from app.models.audit_log import AuditActionType
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.crud.employee import employee_crud
from app.crud.audit_log import audit_log_crud


def _serialize_value(value: Any) -> Any:
    """Serialize value for JSON storage in audit log."""
    if isinstance(value, (Gender, EmployeeStatus)):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    return value


class EmployeeService:
    """Business logic for employee operations with audit logging."""
    
    def get_employee(self, db: Session, employee_id: int) -> Optional[Employee]:
        """Get employee by ID."""
        return employee_crud.get_by_id(db, employee_id)
    
    def get_employee_by_email(self, db: Session, email: str) -> Optional[Employee]:
        """Get employee by email."""
        return employee_crud.get_by_email(db, email)
    
    def get_employees(
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
        """Get paginated employee list."""
        return employee_crud.get_list(
            db, page=page, page_size=page_size, search=search,
            department=department, status=status, sort_by=sort_by, sort_order=sort_order
        )
    
    def get_all_departments(self, db: Session) -> List[str]:
        """Get all departments."""
        return employee_crud.get_all_departments(db)
    
    def get_statistics(self, db: Session) -> dict:
        """Get dashboard statistics."""
        return employee_crud.get_statistics(db)
    
    def _get_changes(self, old: Employee, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get field changes between old employee and new data."""
        changes: Dict[str, Any] = {}
        for field, new_value in new_data.items():
            old_value = getattr(old, field, None)
            old_serialized = _serialize_value(old_value)
            new_serialized = _serialize_value(new_value)
            if old_serialized != new_serialized:
                changes[field] = {"old": old_serialized, "new": new_serialized}
        return changes
    
    def create_employee(self, db: Session, employee_in: EmployeeCreate, operator: User) -> Employee:
        """Create a new employee with audit logging."""
        employee = employee_crud.create(db, employee_in)
        
        employee_data = employee_in.model_dump()
        audit_data: Dict[str, Any] = {}
        for k, v in employee_data.items():
            audit_data[k] = _serialize_value(v)
        
        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.CREATE,
            operator_id=operator.id,
            operator_name=operator.username,
            target_ids=[employee.id],
            changes=audit_data,
            details=f"创建员工: {employee.name} ({employee.employee_id})"
        )
        
        return employee
    
    def update_employee(
        self, db: Session, employee: Employee, employee_in: EmployeeUpdate, operator: User
    ) -> Employee:
        """Update employee with audit logging."""
        update_data = employee_in.model_dump(exclude_unset=True)
        changes = self._get_changes(employee, update_data)
        
        updated_employee = employee_crud.update(db, employee, employee_in)
        
        if changes:
            audit_log_crud.create(
                db=db,
                action_type=AuditActionType.UPDATE,
                operator_id=operator.id,
                operator_name=operator.username,
                target_ids=[employee.id],
                changes=changes,
                details=f"更新员工: {employee.name} ({employee.employee_id})"
            )
        
        return updated_employee
    
    def delete_employee(self, db: Session, employee: Employee, operator: User) -> None:
        """Delete employee with audit logging."""
        employee_name = employee.name
        employee_id_str = employee.employee_id
        employee_id = employee.id
        
        employee_crud.delete(db, employee)
        
        audit_log_crud.create(
            db=db,
            action_type=AuditActionType.DELETE,
            operator_id=operator.id,
            operator_name=operator.username,
            target_ids=[employee_id],
            details=f"删除员工: {employee_name} ({employee_id_str})"
        )
    
    def batch_update_status(
        self,
        db: Session,
        ids: List[int],
        new_status: EmployeeStatus,
        operator: User
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Batch update employee status with validation and audit logging."""
        success_count = 0
        failed_items: List[Dict[str, Any]] = []
        valid_ids: List[int] = []
        all_changes: Dict[str, Any] = {}
        
        employees = employee_crud.get_by_ids(db, ids)
        emp_map = {emp.id: emp for emp in employees}
        
        for emp_id in ids:
            emp = emp_map.get(emp_id)
            if not emp:
                failed_items.append({"id": emp_id, "reason": "员工不存在"})
                continue
            if emp.status == EmployeeStatus.INACTIVE:
                failed_items.append({"id": emp_id, "name": emp.name, "reason": "已离职员工不允许通过批量操作变更状态"})
                continue
            
            old_status = emp.status.value
            emp.status = new_status
            valid_ids.append(emp_id)
            all_changes[str(emp_id)] = {
                "name": emp.name,
                "status": {"old": old_status, "new": new_status.value}
            }
            success_count += 1
        
        if valid_ids:
            db.commit()
            
            audit_log_crud.create(
                db=db,
                action_type=AuditActionType.BATCH_UPDATE_STATUS,
                operator_id=operator.id,
                operator_name=operator.username,
                target_ids=valid_ids,
                changes=all_changes,
                details=f"批量更新状态: {success_count} 人变更为{'在职' if new_status == EmployeeStatus.ACTIVE else '离职'}"
            )
        
        return success_count, failed_items
    
    def batch_delete(
        self, db: Session, ids: List[int], operator: User
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Batch delete employees with audit logging."""
        success_count = 0
        failed_items: List[Dict[str, Any]] = []
        valid_employees: List[Tuple[int, str, str]] = []
        
        employees = employee_crud.get_by_ids(db, ids)
        emp_map = {emp.id: emp for emp in employees}
        
        for emp_id in ids:
            emp = emp_map.get(emp_id)
            if not emp:
                failed_items.append({"id": emp_id, "reason": "员工不存在"})
                continue
            
            valid_employees.append((emp.id, emp.name, emp.employee_id))
            db.delete(emp)
            success_count += 1
        
        if valid_employees:
            db.commit()
            
            deleted_info: Dict[str, Any] = {}
            valid_ids: List[int] = []
            for emp_id, name, emp_id_str in valid_employees:
                valid_ids.append(emp_id)
                deleted_info[str(emp_id)] = {"name": name, "employee_id": emp_id_str}
            
            audit_log_crud.create(
                db=db,
                action_type=AuditActionType.BATCH_DELETE,
                operator_id=operator.id,
                operator_name=operator.username,
                target_ids=valid_ids,
                changes=deleted_info,
                details=f"批量删除: {success_count} 名员工"
            )
        
        return success_count, failed_items
    
    def import_csv(
        self, db: Session, file_content: str, operator: User
    ) -> Dict[str, Any]:
        """Import employees from CSV with audit logging."""
        import csv as csv_module
        import io
        
        gender_map = {"男": Gender.MALE, "女": Gender.FEMALE, "male": Gender.MALE, "female": Gender.FEMALE}
        status_map = {"在职": EmployeeStatus.ACTIVE, "离职": EmployeeStatus.INACTIVE, "active": EmployeeStatus.ACTIVE, "inactive": EmployeeStatus.INACTIVE}
        
        reader = csv_module.reader(io.StringIO(file_content))
        rows = list(reader)
        
        if len(rows) < 2:
            return {"success_count": 0, "failed_count": 0, "failed_items": [], "message": "CSV文件为空或格式不正确"}
        
        success_count = 0
        failed_items: List[Dict[str, Any]] = []
        imported_ids: List[int] = []
        imported_details: List[Dict[str, Any]] = []
        
        for idx, row in enumerate(rows[1:], start=2):
            try:
                if len(row) < 7:
                    failed_items.append({"row": idx, "reason": "必填字段不完整"})
                    continue
                
                _, name, gender_str, age_str, department, position, email, phone, hire_date_str, status_str = (row + [""] * 10)[:10]
                
                name = name.strip()
                email = email.strip()
                department = department.strip()
                position = position.strip()
                
                if not name:
                    failed_items.append({"row": idx, "reason": "姓名不能为空"})
                    continue
                if not email:
                    failed_items.append({"row": idx, "reason": "邮箱不能为空"})
                    continue
                if not department:
                    failed_items.append({"row": idx, "reason": "部门不能为空"})
                    continue
                if not position:
                    failed_items.append({"row": idx, "reason": "职位不能为空"})
                    continue
                
                if employee_crud.get_by_email(db, email):
                    failed_items.append({"row": idx, "data": {"name": name, "email": email}, "reason": "邮箱已存在"})
                    continue
                
                gender = gender_map.get(gender_str.strip())
                if not gender:
                    failed_items.append({"row": idx, "data": {"name": name}, "reason": f"性别格式不正确: {gender_str}"})
                    continue
                
                try:
                    age = int(age_str.strip())
                    if age <= 0 or age > 150:
                        raise ValueError
                except (ValueError, TypeError):
                    failed_items.append({"row": idx, "data": {"name": name}, "reason": f"年龄格式不正确: {age_str}"})
                    continue
                
                try:
                    hire_date = datetime.strptime(hire_date_str.strip(), "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    failed_items.append({"row": idx, "data": {"name": name}, "reason": f"入职日期格式不正确，应为YYYY-MM-DD: {hire_date_str}"})
                    continue
                
                status = status_map.get(status_str.strip(), EmployeeStatus.ACTIVE)
                
                employee_in = EmployeeCreate(
                    name=name,
                    gender=gender,
                    age=age,
                    department=department,
                    position=position,
                    email=email,
                    phone=phone.strip() if phone.strip() else None,
                    hire_date=hire_date,
                    status=status
                )
                
                db_employee = employee_crud.create(db, employee_in)
                
                imported_ids.append(db_employee.id)
                imported_details.append({
                    "name": name,
                    "email": email,
                    "employee_id": db_employee.employee_id
                })
                success_count += 1
                
            except Exception as e:
                failed_items.append({"row": idx, "reason": f"解析错误: {str(e)}"})
        
        if imported_ids:
            audit_log_crud.create(
                db=db,
                action_type=AuditActionType.CSV_IMPORT,
                operator_id=operator.id,
                operator_name=operator.username,
                target_ids=imported_ids,
                changes={"imported_count": success_count, "imported_employees": imported_details},
                details=f"CSV导入: 成功导入 {success_count} 人，失败 {len(failed_items)} 行"
            )
        
        return {
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items
        }


employee_service = EmployeeService()
