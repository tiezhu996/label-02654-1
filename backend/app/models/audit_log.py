"""Audit log model for recording employee management operations."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Audit action enumeration."""
    CREATE = "create"            # 新增员工
    UPDATE = "update"            # 修改员工
    DELETE = "delete"            # 删除员工
    BULK_UPDATE = "bulk_update"  # 批量改状态
    BULK_DELETE = "bulk_delete"  # 批量删除
    IMPORT = "import"            # CSV 导入


class AuditLog(Base):
    """Audit log model for storing operation records."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)  # 操作类型
    operator_id = Column(Integer, nullable=False, index=True)          # 操作人ID(User.id)
    operator_name = Column(String(100), nullable=False)                # 操作人用户名(冗余便于展示)
    target_type = Column(String(50), nullable=False)                   # 资源类型,固定为 employee
    target_id = Column(String(100), nullable=True, index=True)         # 资源主键(单条时是 employee.id)
    target_name = Column(String(100), nullable=True)                   # 资源名称(姓名,便于展示)
    changes = Column(Text, nullable=True)                              # 关键字段变更, JSON 字符串
    summary = Column(String(255), nullable=True)                       # 简要说明(批量操作影响数量等)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
