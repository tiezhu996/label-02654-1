"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient as StarletteTestClient

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.employee import Employee, Gender, EmployeeStatus
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash
from datetime import date

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    try:
        with TestClient(app) as test_client:
            yield test_client
    except TypeError:
        with StarletteTestClient(app) as test_client:
            yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def normal_user(db_session):
    """Create a normal user for testing."""
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("user123"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """Get admin JWT token."""
    response = client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def user_token(client, normal_user):
    """Get normal user JWT token."""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "user123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def sample_employee(db_session):
    """Create a sample employee for testing."""
    employee = Employee(
        employee_id="EMP20260101TEST01",
        name="测试员工",
        gender=Gender.MALE,
        age=30,
        department="技术部",
        position="工程师",
        email="t***@***********",
        phone="138******00",
        hire_date=date(2024, 1, 1),
        status=EmployeeStatus.ACTIVE
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture(scope="function")
def sample_inactive_employee(db_session):
    """Create an inactive sample employee for testing."""
    employee = Employee(
        employee_id="EMP20260101TEST02",
        name="离职员工",
        gender=Gender.FEMALE,
        age=28,
        department="市场部",
        position="专员",
        email="i******@***********",
        phone="138******01",
        hire_date=date(2023, 6, 1),
        status=EmployeeStatus.INACTIVE
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee
