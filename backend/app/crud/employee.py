"""CRUD operations for Employee model."""

from sqlalchemy.orm import Session
from sqlalchemy import or_, func, extract
from typing import Optional, List, Tuple, Dict, Any, Iterable
from datetime import datetime, date
import csv
import io
import uuid

from pydantic import ValidationError

from app.models.employee import Employee, Gender, EmployeeStatus
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    BulkOperationResult,
    CsvImportResult,
    CsvImportRowError,
)
from app.crud.audit_log import audit_log_crud


# CSV import: 中文表头 -> 模型字段
CSV_HEADER_MAP: Dict[str, str] = {
    "工号": "employee_id",
    "姓名": "name",
    "性别": "gender",
    "年龄": "age",
    "部门": "department",
    "职位": "position",
    "邮箱": "email",
    "电话": "phone",
    "入职日期": "hire_date",
    "状态": "status",
}

# CSV import: 中文枚举值映射
CSV_GENDER_MAP: Dict[str, str] = {"男": "male", "女": "female"}
CSV_STATUS_MAP: Dict[str, str] = {"在职": "active", "离职": "inactive"}

# 必填字段(同导出表头一致,工号为系统生成,允许 CSV 中携带或为空)
REQUIRED_FIELDS: Tuple[str, ...] = (
    "name",
    "gender",
    "age",
    "department",
    "position",
    "email",
    "hire_date",
)

# 审计日志中需要追踪变化的关键字段
AUDIT_TRACKED_FIELDS: Tuple[str, ...] = (
    "name",
    "gender",
    "age",
    "department",
    "position",
    "email",
    "phone",
    "hire_date",
    "status",
)


class EmployeeCRUD:
    """CRUD operations for Employee."""

    def _generate_employee_id(self) -> str:
        """Generate a unique employee ID."""
        return f"EMP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"

    def get_by_id(self, db: Session, employee_id: int) -> Optional[Employee]:
        """Get employee by ID."""
        return db.query(Employee).filter(Employee.id == employee_id).first()

    def get_by_employee_id(self, db: Session, employee_id: str) -> Optional[Employee]:
        """Get employee by employee_id (工号)."""
        return db.query(Employee).filter(Employee.employee_id == employee_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
        """Get employee by email."""
        return db.query(Employee).filter(Employee.email == email).first()

    def get_by_ids(self, db: Session, ids: Iterable[int]) -> List[Employee]:
        """Get employees by a list of primary key ids."""
        ids_list = list(ids)
        if not ids_list:
            return []
        return db.query(Employee).filter(Employee.id.in_(ids_list)).all()

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
        """Get paginated list of employees with filters."""
        query = db.query(Employee)

        # Apply search filter
        if search:
            search_filter = or_(
                Employee.name.ilike(f"%{search}%"),
                Employee.employee_id.ilike(f"%{search}%"),
                Employee.department.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Apply department filter
        if department:
            query = query.filter(Employee.department == department)

        # Apply status filter
        if status:
            query = query.filter(Employee.status == status)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = getattr(Employee, sort_by, Employee.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        employees = query.offset(offset).limit(page_size).all()

        return employees, total

    def create(
        self,
        db: Session,
        employee_in: EmployeeCreate,
        operator: Optional[User] = None,
    ) -> Employee:
        """Create a new employee and write audit log in business layer."""
        db_employee = Employee(
            employee_id=self._generate_employee_id(),
            **employee_in.model_dump()
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)

        if operator is not None:
            audit_log_crud.create(
                db,
                action=AuditAction.CREATE,
                operator_id=operator.id,
                operator_name=operator.username,
                target_id=db_employee.id,
                target_name=db_employee.name,
                changes={
                    field: self._serialize_value(getattr(db_employee, field))
                    for field in AUDIT_TRACKED_FIELDS
                },
                summary=f"创建员工 {db_employee.name}({db_employee.employee_id})",
            )
        return db_employee

    def update(
        self,
        db: Session,
        employee: Employee,
        employee_in: EmployeeUpdate,
        operator: Optional[User] = None,
    ) -> Employee:
        """Update an existing employee and write audit log in business layer."""
        update_data = employee_in.model_dump(exclude_unset=True)

        # 记录修改前后的关键字段差异
        changes: Dict[str, Dict[str, Any]] = {}
        for field, new_value in update_data.items():
            if field not in AUDIT_TRACKED_FIELDS:
                continue
            old_value = getattr(employee, field, None)
            if old_value != new_value:
                changes[field] = {
                    "old": self._serialize_value(old_value),
                    "new": self._serialize_value(new_value),
                }

        for field, value in update_data.items():
            setattr(employee, field, value)

        db.commit()
        db.refresh(employee)

        if operator is not None and changes:
            audit_log_crud.create(
                db,
                action=AuditAction.UPDATE,
                operator_id=operator.id,
                operator_name=operator.username,
                target_id=employee.id,
                target_name=employee.name,
                changes=changes,
                summary=f"修改员工 {employee.name}({employee.employee_id})",
            )
        return employee

    def delete(
        self,
        db: Session,
        employee: Employee,
        operator: Optional[User] = None,
    ) -> None:
        """Delete an employee and write audit log in business layer."""
        # 删除前先收集快照
        snapshot = {
            field: self._serialize_value(getattr(employee, field))
            for field in AUDIT_TRACKED_FIELDS
        }
        target_id = employee.id
        target_name = employee.name
        target_employee_id = employee.employee_id

        db.delete(employee)
        db.commit()

        if operator is not None:
            audit_log_crud.create(
                db,
                action=AuditAction.DELETE,
                operator_id=operator.id,
                operator_name=operator.username,
                target_id=target_id,
                target_name=target_name,
                changes=snapshot,
                summary=f"删除员工 {target_name}({target_employee_id})",
            )

    def bulk_update_status(
        self,
        db: Session,
        ids: List[int],
        new_status: EmployeeStatus,
        operator: User,
    ) -> BulkOperationResult:
        """
        Bulk update employee status.
        Already-inactive employees are NOT allowed to be modified via bulk operation.
        """
        success_ids: List[int] = []
        failed_items: List[dict] = []

        employees = self.get_by_ids(db, ids)
        found_map = {emp.id: emp for emp in employees}

        for emp_id in ids:
            emp = found_map.get(emp_id)
            if emp is None:
                failed_items.append({"id": emp_id, "reason": "员工不存在"})
                continue
            # 业务规则: 已离职员工禁止通过批量操作变更状态
            if emp.status == EmployeeStatus.INACTIVE:
                failed_items.append({"id": emp_id, "reason": "已离职员工不允许通过批量操作变更状态"})
                continue
            emp.status = new_status
            success_ids.append(emp_id)

        if success_ids:
            db.commit()

        # 业务层写审计日志: 单条聚合记录,记录受影响的 ID 列表
        audit_log_crud.create(
            db,
            action=AuditAction.BULK_UPDATE,
            operator_id=operator.id,
            operator_name=operator.username,
            target_id=None,
            target_name=None,
            changes={
                "status": new_status.value,
                "affected_ids": success_ids,
                "failed_items": failed_items,
            },
            summary=(
                f"批量修改状态为 {new_status.value},"
                f" 成功 {len(success_ids)} 条,失败 {len(failed_items)} 条"
            ),
        )

        return BulkOperationResult(
            success_count=len(success_ids),
            failed_count=len(failed_items),
            failed_items=failed_items,
        )

    def bulk_delete(
        self,
        db: Session,
        ids: List[int],
        operator: User,
    ) -> BulkOperationResult:
        """Bulk delete employees."""
        success_items: List[dict] = []
        failed_items: List[dict] = []

        employees = self.get_by_ids(db, ids)
        found_map = {emp.id: emp for emp in employees}

        for emp_id in ids:
            emp = found_map.get(emp_id)
            if emp is None:
                failed_items.append({"id": emp_id, "reason": "员工不存在"})
                continue
            success_items.append({
                "id": emp.id,
                "employee_id": emp.employee_id,
                "name": emp.name,
            })
            db.delete(emp)

        if success_items:
            db.commit()

        audit_log_crud.create(
            db,
            action=AuditAction.BULK_DELETE,
            operator_id=operator.id,
            operator_name=operator.username,
            target_id=None,
            target_name=None,
            changes={
                "deleted": success_items,
                "failed_items": failed_items,
            },
            summary=(
                f"批量删除员工,成功 {len(success_items)} 条,"
                f"失败 {len(failed_items)} 条"
            ),
        )

        return BulkOperationResult(
            success_count=len(success_items),
            failed_count=len(failed_items),
            failed_items=failed_items,
        )

    def import_from_csv(
        self,
        db: Session,
        csv_bytes: bytes,
        operator: User,
    ) -> CsvImportResult:
        """
        Import employees from a CSV file (same format as export).
        Each row is validated independently. Errors do not abort the batch.
        """
        # 容错读取: 优先 utf-8-sig (兼容带 BOM),失败回退 gbk
        text: str
        try:
            text = csv_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = csv_bytes.decode("gbk", errors="replace")

        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return CsvImportResult(success_count=0, failed_count=0, errors=[])

        header = [h.strip() for h in rows[0]]
        # 把中文表头映射到模型字段(允许包含未识别的列,只做忽略)
        col_fields: List[Optional[str]] = [CSV_HEADER_MAP.get(h) for h in header]

        success_count = 0
        errors: List[CsvImportRowError] = []

        # row index 从第 2 行开始(第 1 行是表头),便于用户在 Excel 中定位
        for row_no, raw in enumerate(rows[1:], start=2):
            if not any((cell or "").strip() for cell in raw):
                continue  # 跳过空行
            try:
                payload = self._build_payload_from_row(raw, col_fields)
                # 必填字段
                missing = [f for f in REQUIRED_FIELDS if not payload.get(f)]
                if missing:
                    raise ValueError(f"必填字段缺失: {', '.join(missing)}")
                # 邮箱唯一性(逐行独立校验)
                email = payload.get("email")
                if email and self.get_by_email(db, email=email):
                    raise ValueError(f"邮箱已存在: {email}")
                # 通过 Pydantic 完成类型/格式校验
                employee_in = EmployeeCreate(**payload)
                # 直接落库, CSV 导入聚合写一条审计日志,不为每行写
                db_employee = Employee(
                    employee_id=self._generate_employee_id(),
                    **employee_in.model_dump(),
                )
                db.add(db_employee)
                db.commit()
                db.refresh(db_employee)
                success_count += 1
            except ValidationError as exc:
                db.rollback()
                errors.append(CsvImportRowError(row=row_no, reason=self._format_validation_error(exc)))
            except ValueError as exc:
                db.rollback()
                errors.append(CsvImportRowError(row=row_no, reason=str(exc)))
            except Exception as exc:  # noqa: BLE001 - 兜底,避免单行错误阻断
                db.rollback()
                errors.append(CsvImportRowError(row=row_no, reason=f"未知错误: {exc}"))

        audit_log_crud.create(
            db,
            action=AuditAction.IMPORT,
            operator_id=operator.id,
            operator_name=operator.username,
            target_id=None,
            target_name=None,
            changes={
                "success_count": success_count,
                "failed_count": len(errors),
                "errors": [e.model_dump() for e in errors],
            },
            summary=f"CSV 导入员工,成功 {success_count} 条,失败 {len(errors)} 条",
        )

        return CsvImportResult(
            success_count=success_count,
            failed_count=len(errors),
            errors=errors,
        )

    def get_all_departments(self, db: Session) -> List[str]:
        """Get all unique departments."""
        result = db.query(Employee.department).distinct().all()
        return [r[0] for r in result]

    def get_statistics(self, db: Session) -> dict:
        """Get employee statistics for dashboard."""
        # Total employees
        total = db.query(Employee).count()

        # Active employees
        active = db.query(Employee).filter(Employee.status == EmployeeStatus.ACTIVE).count()

        # Inactive employees
        inactive = db.query(Employee).filter(Employee.status == EmployeeStatus.INACTIVE).count()

        # This month new hires
        now = datetime.now()
        this_month_hires = db.query(Employee).filter(
            extract('year', Employee.hire_date) == now.year,
            extract('month', Employee.hire_date) == now.month
        ).count()

        # Gender distribution
        male_count = db.query(Employee).filter(Employee.gender == Gender.MALE).count()
        female_count = db.query(Employee).filter(Employee.gender == Gender.FEMALE).count()

        # Department distribution
        dept_stats = db.query(
            Employee.department,
            func.count(Employee.id)
        ).group_by(Employee.department).all()

        # Monthly hire trend (last 12 months)
        hire_trend = []
        for i in range(11, -1, -1):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1

            count = db.query(Employee).filter(
                extract('year', Employee.hire_date) == year,
                extract('month', Employee.hire_date) == month
            ).count()

            hire_trend.append({
                "month": f"{year}-{month:02d}",
                "count": count
            })

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "this_month_hires": this_month_hires,
            "active_rate": round(active / total * 100, 1) if total > 0 else 0,
            "gender_distribution": {
                "male": male_count,
                "female": female_count
            },
            "department_distribution": [
                {"department": dept, "count": count}
                for dept, count in dept_stats
            ],
            "hire_trend": hire_trend
        }

    # ---------------- helpers ----------------

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize a value for audit log JSON storage."""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if hasattr(value, "value"):  # enum
            return value.value
        return value

    def _build_payload_from_row(
        self,
        raw: List[str],
        col_fields: List[Optional[str]],
    ) -> Dict[str, Any]:
        """Convert a CSV row into a payload dict suitable for EmployeeCreate."""
        payload: Dict[str, Any] = {}
        for idx, field in enumerate(col_fields):
            if field is None or idx >= len(raw):
                continue
            value = (raw[idx] or "").strip()
            if value == "":
                continue
            if field == "gender":
                payload[field] = CSV_GENDER_MAP.get(value, value).lower()
            elif field == "status":
                payload[field] = CSV_STATUS_MAP.get(value, value).lower()
            elif field == "age":
                try:
                    payload[field] = int(value)
                except ValueError as exc:
                    raise ValueError(f"年龄格式不正确: {value}") from exc
            elif field == "hire_date":
                payload[field] = self._parse_date(value)
            elif field == "employee_id":
                # 工号由系统生成,忽略 CSV 中的工号
                continue
            else:
                payload[field] = value
        return payload

    @staticmethod
    def _parse_date(value: str) -> date:
        """Parse a date string in common formats."""
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"入职日期格式不正确: {value}")

    @staticmethod
    def _format_validation_error(exc: ValidationError) -> str:
        """Format pydantic ValidationError into a short Chinese message."""
        details = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []))
            msg = err.get("msg", "")
            details.append(f"{loc}: {msg}")
        return "; ".join(details) or "字段校验失败"


employee_crud = EmployeeCRUD()
