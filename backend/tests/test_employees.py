"""Tests for employee API."""

import pytest


class TestEmployeeList:
    """Tests for employee list endpoint."""

    def test_get_employees_empty(self, client, admin_token):
        """Test getting empty employee list."""
        response = client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_employees_with_data(self, client, admin_token, sample_employee):
        """Test getting employee list with data."""
        response = client.get(
            "/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "测试员工"

    def test_get_employees_pagination(self, client, admin_token, sample_employee):
        """Test employee list pagination."""
        response = client.get(
            "/api/employees?page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_get_employees_filter_by_department(self, client, admin_token, sample_employee):
        """Test filtering employees by department."""
        response = client.get(
            "/api/employees?department=技术部",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_employees_filter_by_status(self, client, admin_token, sample_employee):
        """Test filtering employees by status."""
        response = client.get(
            "/api/employees?status=active",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_employees_unauthorized(self, client):
        """Test getting employees without authentication."""
        response = client.get("/api/employees")
        assert response.status_code == 403


class TestEmployeeCreate:
    """Tests for employee create endpoint."""

    def test_create_employee_success(self, client, admin_token):
        """Test creating a new employee."""
        response = client.post(
            "/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "新员工",
                "gender": "male",
                "age": 25,
                "department": "产品部",
                "position": "产品经理",
                "email": "new@example.com",
                "hire_date": "2024-06-01"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "新员工"
        assert data["department"] == "产品部"
        assert "employee_id" in data

    def test_create_employee_duplicate_email(self, client, admin_token, sample_employee):
        """Test creating employee with duplicate email."""
        response = client.post(
            "/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "另一个员工",
                "gender": "female",
                "age": 28,
                "department": "市场部",
                "position": "市场专员",
                "email": "test@example.com",  # Duplicate
                "hire_date": "2024-06-01"
            }
        )
        assert response.status_code == 400
        assert "邮箱已被使用" in response.json()["detail"]

    def test_create_employee_by_normal_user(self, client, user_token):
        """Test that normal user cannot create employee."""
        response = client.post(
            "/api/employees",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "新员工",
                "gender": "male",
                "age": 25,
                "department": "产品部",
                "position": "产品经理",
                "email": "new@example.com",
                "hire_date": "2024-06-01"
            }
        )
        assert response.status_code == 403
        assert "需要管理员权限" in response.json()["detail"]


class TestEmployeeDetail:
    """Tests for employee detail endpoint."""

    def test_get_employee_success(self, client, admin_token, sample_employee):
        """Test getting employee details."""
        response = client.get(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试员工"

    def test_get_employee_not_found(self, client, admin_token):
        """Test getting non-existent employee."""
        response = client.get(
            "/api/employees/9999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404


class TestEmployeeUpdate:
    """Tests for employee update endpoint."""

    def test_update_employee_success(self, client, admin_token, sample_employee):
        """Test updating employee info."""
        response = client.put(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"position": "高级工程师", "age": 31}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == "高级工程师"
        assert data["age"] == 31

    def test_update_employee_not_found(self, client, admin_token):
        """Test updating non-existent employee."""
        response = client.put(
            "/api/employees/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"position": "高级工程师"}
        )
        assert response.status_code == 404

    def test_update_employee_by_normal_user(self, client, user_token, sample_employee):
        """Test that normal user cannot update employee."""
        response = client.put(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"position": "高级工程师"}
        )
        assert response.status_code == 403


class TestEmployeeDelete:
    """Tests for employee delete endpoint."""

    def test_delete_employee_success(self, client, admin_token, sample_employee):
        """Test deleting an employee."""
        response = client.delete(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 204

        # Verify deletion
        response = client.get(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_delete_employee_not_found(self, client, admin_token):
        """Test deleting non-existent employee."""
        response = client.delete(
            "/api/employees/9999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_delete_employee_by_normal_user(self, client, user_token, sample_employee):
        """Test that normal user cannot delete employee."""
        response = client.delete(
            f"/api/employees/{sample_employee.id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403


class TestEmployeeStatistics:
    """Tests for employee statistics endpoint."""

    def test_get_statistics_empty(self, client, admin_token):
        """Test statistics with no employees."""
        response = client.get(
            "/api/employees/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_get_statistics_with_data(self, client, admin_token, sample_employee):
        """Test statistics with employee data."""
        response = client.get(
            "/api/employees/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["active"] == 1
        assert "gender_distribution" in data
        assert "department_distribution" in data
        assert "hire_trend" in data


class TestEmployeeDepartments:
    """Tests for departments list endpoint."""

    def test_get_departments_empty(self, client, admin_token):
        """Test getting departments when empty."""
        response = client.get(
            "/api/employees/departments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["departments"] == []

    def test_get_departments_with_data(self, client, admin_token, sample_employee):
        """Test getting departments with data."""
        response = client.get(
            "/api/employees/departments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "技术部" in data["departments"]


class TestEmployeeExport:
    """Tests for employee CSV export endpoint."""

    def test_export_csv(self, client, admin_token, sample_employee):
        """Test CSV export."""
        response = client.get(
            "/api/employees/export",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        content = response.content.decode("utf-8")
        assert "工号" in content
        assert "测试员工" in content
