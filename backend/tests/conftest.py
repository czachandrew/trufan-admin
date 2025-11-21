import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings


# Use PostgreSQL database - tests run in Docker, so use db:5432
# The settings.DATABASE_URL already points to db:5432 from docker-compose.yml
engine = create_engine(settings.DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """Create database session for testing."""
    # Tables already exist from migrations, no need to create
    db = TestingSessionLocal()
    try:
        yield db
        # Rollback any changes made during test
        db.rollback()
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """Create test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing with unique email."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test-{unique_id}@example.com",
        "password": "TestPassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone": f"+1234567{unique_id[:4]}",
    }


@pytest.fixture
def test_user(client, test_user_data):
    """Create a test user and return it."""
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    return {"Authorization": f"Bearer {test_user['access_token']}"}
