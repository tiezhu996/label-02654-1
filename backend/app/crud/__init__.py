# CRUD module
from app.crud.user import user_crud
from app.crud.employee import employee_crud
from app.crud.audit_log import audit_log_crud

__all__ = ["user_crud", "employee_crud", "audit_log_crud"]
