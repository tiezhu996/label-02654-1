"""Tests for new features: audit logs, batch operations, CSV import."""

import io

from app.models.audit_log import AuditLog, AuditActionType
from app.models.employee import EmployeeStatus


class TestAuditLoggingOnCreate:
    """Test audit logging when creating employees."""

    def test_create_employee_logs_audit(self, client, admin_token, admin_user, db_session):
        """Test that creating an employee creates an audit log entry."""
        employee_data = {
            "name": "新员工",
            "gender": "male",
            "age": 25,
            "department": "技术部",
            "position": "开发工程师",
            "email": "newemployee@example.com",
            "phone": "139******00",
            "hire_date": "2026-01-15",
            "status": "active"
        }

        response = client.post(
            "/api/employees",
            json=employee_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "新员工"

        logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.CREATE
        ).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.operator_id == admin_user.id
        assert log.operator_name == admin_user.full_name
        assert log.target_name == "新员工"
        assert log.changes is not None
        assert "姓名" in log.changes
        assert log.changes["姓名"]["new"] == "新员工"
        assert "邮箱" in log.changes
        assert log.changes["邮箱"]["new"] == "newemployee@example.com"
        assert "性别" in log.changes
        assert log.changes["性别"]["new"] == "male"
        assert "入职日期" in log.changes
        assert log.changes["入职日期"]["new"] == "2026-01-15"

    def test_update_employee_logs_changes(self, client, admin_token, sample_employee, db_session):
        """Test that updating an employee logs the changed fields."""
        update_data = {
            "name": "改名员工",
            "position": "高级工程师",
            "department": "产品部"
        }

        response = client.put(
            f"/api/employees/{sample_employee.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200

        logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.UPDATE
        ).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.target_ids == [sample_employee.id]
        assert log.changes is not None
        assert "姓名" in log.changes
        assert log.changes["姓名"]["old"] == "测试员工"
        assert log.changes["姓名"]["new"] == "改名员工"
        assert "部门" in log.changes
        assert log.changes["部门"]["old"] == "技术部"
        assert log.changes["部门"]["new"] == "产品部"
        assert "职位" in log.changes
        assert log.changes["职位"]["old"] == "工程师"
        assert log.changes["职位"]["new"] == "高级工程师"

    def test_delete_employee_logs_audit(self, client, admin_token, sample_employee, db_session):
        """Test that deleting an employee creates an audit log."""
        response = client.delete(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 204

        logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.DELETE
        ).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.target_ids == [sample_employee.id]
        assert log.target_name == "测试员工"
        assert log.changes is not None
        assert "工号" in log.changes
        assert log.changes["工号"]["old"] == sample_employee.employee_id


class TestBatchOperations:
    """Test batch operations for employees."""

    def test_batch_set_inactive_success(self, client, admin_token, sample_employee, db_session):
        """Test batch setting employees to inactive status."""
        response = client.post(
            "/api/employees/batch/status",
            json={"ids": [sample_employee.id], "status": "inactive"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 0

        emp = db_session.query(type(sample_employee)).get(sample_employee.id)
        assert emp.status == EmployeeStatus.INACTIVE

        logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.BATCH_UPDATE_STATUS
        ).all()
        assert len(logs) == 1
        assert logs[0].target_ids == [sample_employee.id]

    def test_batch_inactive_cannot_be_set_to_active(self, client, admin_token, sample_inactive_employee, db_session):
        """Test that already inactive employees cannot be changed via batch status operation."""
        response = client.post(
            "/api/employees/batch/status",
            json={"ids": [sample_inactive_employee.id], "status": "active"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["failed_count"] == 1
        assert "已是离职状态" in data["errors"][0]["message"]

        emp = db_session.query(type(sample_inactive_employee)).get(sample_inactive_employee.id)
        assert emp.status == EmployeeStatus.INACTIVE

    def test_batch_set_same_status_fails(self, client, admin_token, sample_employee, db_session):
        """Test that setting same status is counted as failure."""
        response = client.post(
            "/api/employees/batch/status",
            json={"ids": [sample_employee.id], "status": "active"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["failed_count"] == 1
        assert "已是在职状态" in data["errors"][0]["message"]

    def test_batch_nonexistent_employee_fails(self, client, admin_token, db_session):
        """Test that batch operation with non-existent IDs reports errors."""
        response = client.post(
            "/api/employees/batch/status",
            json={"ids": [9999], "status": "inactive"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["failed_count"] == 1
        assert data["errors"][0]["message"] == "员工不存在"

    def test_batch_delete_success(self, client, admin_token, sample_employee, db_session):
        """Test batch deleting employees."""
        response = client.post(
            "/api/employees/batch/delete",
            json={"ids": [sample_employee.id]},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 0

        emp = db_session.query(type(sample_employee)).filter_by(id=sample_employee.id).first()
        assert emp is None

        logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.BATCH_DELETE
        ).all()
        assert len(logs) == 1

    def test_batch_operation_requires_admin(self, client, user_token, sample_employee):
        """Test that batch operations require admin privileges."""
        response = client.post(
            "/api/employees/batch/status",
            json={"ids": [sample_employee.id], "status": "inactive"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    def test_batch_mixed_success_and_failure(self, client, admin_token, sample_employee, sample_inactive_employee, db_session):
        """Test batch operation with mix of valid and invalid employees."""
        response = client.post(
            "/api/employees/batch/status",
            json={"ids": [sample_employee.id, sample_inactive_employee.id, 9999], "status": "inactive"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 2
        assert len(data["errors"]) == 2


class TestCsvImport:
    """Test CSV import functionality."""

    def test_csv_import_success(self, client, admin_token, db_session):
        """Test successful CSV import."""
        output = io.StringIO()
        output.write("工号,姓名,性别,年龄,部门,职位,邮箱,电话,入职日期,状态\n")
        output.write(",张三,男,28,技术部,工程师,zhangsan@example.com,138******11,2026-01-01,在职\n")
        output.write(",李四,女,32,市场部,经理,lisi@example.com,138******22,2026-02-01,在职\n")
        csv_content = output.getvalue()

        response = client.post(
            "/api/employees/import",
            files={"file": ("employees.csv", csv_content.encode("utf-8-sig"), "text/csv")},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2
        assert data["failed_count"] == 0
        assert data["total_count"] == 2
        assert all(r["success"] for r in data["results"])

        logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.IMPORT
        ).all()
        assert len(logs) == 1
        assert "CSV导入完成" in logs[0].details

        create_logs = db_session.query(AuditLog).filter(
            AuditLog.action_type == AuditActionType.CREATE
        ).all()
        assert len(create_logs) == 2

    def test_csv_import_partial_failure(self, client, admin_token, sample_employee, db_session):
        """Test CSV import with some rows failing."""
        output = io.StringIO()
        output.write("工号,姓名,性别,年龄,部门,职位,邮箱,电话,入职日期,状态\n")
        output.write(",王五,男,30,产品部,产品经理,wangwu@example.com,138******33,2026-03-01,在职\n")
        output.write(",重复邮箱,男,35,测试部,测试,test@example.com,138******44,2026-03-15,在职\n")
        output.write(",,,,,,,,,\n")
        csv_content = output.getvalue()

        response = client.post(
            "/api/employees/import",
            files={"file": ("employees.csv", csv_content.encode("utf-8"), "text/csv")},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 2
        assert data["total_count"] == 3

        failed_rows = [r for r in data["results"] if not r["success"]]
        assert len(failed_rows) == 2
        assert any("邮箱已存在" in r["message"] for r in failed_rows)
        assert any("姓名不能为空" in r["message"] for r in failed_rows)

    def test_csv_import_chinese_headers_and_values(self, client, admin_token, db_session):
        """Test CSV with Chinese headers and values works correctly."""
        output = io.StringIO()
        output.write("工号,姓名,性别,年龄,部门,职位,邮箱,电话,入职日期,状态\n")
        output.write("EMP001,赵六,男,40,人事部,总监,zhaoliu@example.com,,2020-05-20,离职\n")
        csv_content = output.getvalue()

        response = client.post(
            "/api/employees/import",
            files={"file": ("employees.csv", csv_content.encode("gbk"), "text/csv")},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["results"][0]["success"] is True

    def test_csv_import_requires_admin(self, client, user_token):
        """Test that CSV import requires admin privileges."""
        csv_content = "工号,姓名,性别,年龄,部门,职位,邮箱,电话,入职日期,状态\n,test,男,25,test,test,t**@test.com,,2026-01-01,在职\n"
        response = client.post(
            "/api/employees/import",
            files={"file": ("employees.csv", csv_content.encode(), "text/csv")},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestAuditLogApi:
    """Test audit log API endpoints."""

    def test_get_audit_logs_as_admin(self, client, admin_token, sample_employee):
        """Test that admin can view audit logs."""
        client.delete(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_get_audit_logs_requires_admin(self, client, user_token):
        """Test that normal users cannot access audit logs."""
        response = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    def test_get_audit_logs_filter_by_type(self, client, admin_token, sample_employee, db_session):
        """Test filtering audit logs by action type."""
        client.delete(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        response = client.get(
            "/api/audit-logs?action_type=delete",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(item["action_type"] == "delete" for item in data["items"])

    def test_get_audit_logs_pagination(self, client, admin_token, db_session):
        """Test audit log pagination."""
        for i in range(5):
            emp_data = {
                "name": f"员工{i}",
                "gender": "male",
                "age": 25 + i,
                "department": "测试部",
                "position": "测试",
                "email": f"emp{i}@example.com",
                "hire_date": "2026-01-01"
            }
            client.post(
                "/api/employees",
                json=emp_data,
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        response = client.get(
            "/api/audit-logs?page=1&page_size=3",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert data["total"] >= 5
        assert data["total_pages"] >= 2

    def test_audit_log_fields_are_serializable(self, client, admin_token, db_session):
        """Test that audit log changes are JSON serializable with proper types."""
        emp_data = {
            "name": "序列化测试",
            "gender": "female",
            "age": 26,
            "department": "测试部",
            "position": "测试工程师",
            "email": "serialtest@example.com",
            "hire_date": "2026-06-01",
            "status": "active"
        }
        client.post(
            "/api/employees",
            json=emp_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        response = client.get(
            "/api/audit-logs?action_type=create",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        log = data["items"][0]
        assert log["changes"] is not None
        assert isinstance(log["changes"]["性别"]["new"], str)
        assert log["changes"]["性别"]["new"] == "female"
        assert isinstance(log["changes"]["入职日期"]["new"], str)
        assert log["changes"]["入职日期"]["new"] == "2026-06-01"
