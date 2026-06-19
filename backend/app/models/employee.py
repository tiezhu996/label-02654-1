"""Employee model for employee management."""

from sqlalchemy import Column, Integer, String, Date, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class Gender(str, enum.Enum):
    """Gender enumeration."""
    MALE = "male"
    FEMALE = "female"


class EmployeeStatus(str, enum.Enum):
    """Employee status enumeration."""
    ACTIVE = "active"      # 在职
    INACTIVE = "inactive"  # 离职


class Employee(Base):
    """Employee model for storing employee information."""
    
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(20), unique=True, index=True, nullable=False)  # 工号
    name = Column(String(50), nullable=False, index=True)  # 姓名
    gender = Column(SQLEnum(Gender), nullable=False)  # 性别
    age = Column(Integer, nullable=False)  # 年龄
    department = Column(String(50), nullable=False, index=True)  # 部门
    position = Column(String(50), nullable=False)  # 职位
    email = Column(String(100), unique=True, nullable=False)  # 邮箱
    phone = Column(String(20), nullable=True)  # 电话
    hire_date = Column(Date, nullable=False)  # 入职日期
    status = Column(SQLEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False)  # 状态
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
