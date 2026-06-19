"""CRUD operations for Employee model - pure data access layer."""

from sqlalchemy.orm import Session
from sqlalchemy import or_, func, extract
from typing import Optional, List, Tuple
from datetime import datetime
import uuid

from app.models.employee import Employee, Gender, EmployeeStatus
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeCRUD:
    """Pure data access operations for Employee - no business logic or audit."""
    
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
    
    def get_by_ids(self, db: Session, ids: List[int]) -> List[Employee]:
        """Get employees by list of IDs."""
        return db.query(Employee).filter(Employee.id.in_(ids)).all()
    
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
        
        if search:
            search_filter = or_(
                Employee.name.ilike(f"%{search}%"),
                Employee.employee_id.ilike(f"%{search}%"),
                Employee.department.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if department:
            query = query.filter(Employee.department == department)
        
        if status:
            query = query.filter(Employee.status == status)
        
        total = query.count()
        
        sort_column = getattr(Employee, sort_by, Employee.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        offset = (page - 1) * page_size
        employees = query.offset(offset).limit(page_size).all()
        
        return employees, total
    
    def create(self, db: Session, employee_in: EmployeeCreate) -> Employee:
        """Create a new employee (pure data access)."""
        db_employee = Employee(
            employee_id=self._generate_employee_id(),
            **employee_in.model_dump()
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    
    def update(self, db: Session, employee: Employee, employee_in: EmployeeUpdate) -> Employee:
        """Update an existing employee (pure data access)."""
        update_data = employee_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)
        db.commit()
        db.refresh(employee)
        return employee
    
    def delete(self, db: Session, employee: Employee) -> None:
        """Delete an employee (pure data access)."""
        db.delete(employee)
        db.commit()
    
    def get_all_departments(self, db: Session) -> List[str]:
        """Get all unique departments."""
        result = db.query(Employee.department).distinct().all()
        return [r[0] for r in result]
    
    def get_statistics(self, db: Session) -> dict:
        """Get employee statistics for dashboard."""
        total = db.query(Employee).count()
        active = db.query(Employee).filter(Employee.status == EmployeeStatus.ACTIVE).count()
        inactive = db.query(Employee).filter(Employee.status == EmployeeStatus.INACTIVE).count()
        
        now = datetime.now()
        this_month_hires = db.query(Employee).filter(
            extract('year', Employee.hire_date) == now.year,
            extract('month', Employee.hire_date) == now.month
        ).count()
        
        male_count = db.query(Employee).filter(Employee.gender == Gender.MALE).count()
        female_count = db.query(Employee).filter(Employee.gender == Gender.FEMALE).count()
        
        dept_stats = db.query(
            Employee.department,
            func.count(Employee.id)
        ).group_by(Employee.department).all()
        
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


employee_crud = EmployeeCRUD()
