"""Tests for authentication API."""

import pytest


class TestAuthLogin:
    """Tests for login endpoint."""

    def test_login_success(self, client, admin_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testadmin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={"username": "testadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == 401


class TestAuthRegister:
    """Tests for register endpoint."""

    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"

    def test_register_duplicate_username(self, client, admin_user):
        """Test registration with duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testadmin",
                "email": "another@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_register_duplicate_email(self, client, admin_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "another",
                "email": "testadmin@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "邮箱已被注册" in response.json()["detail"]


class TestAuthMe:
    """Tests for current user endpoint."""

    def test_get_me_success(self, client, admin_token):
        """Test getting current user info."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"

    def test_get_me_unauthorized(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
