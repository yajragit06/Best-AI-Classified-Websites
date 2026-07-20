"""Shared test fixtures.

API tests run the real FastAPI app against an in-memory SQLite database via a
dependency override, so no PostgreSQL instance is required in CI.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core.rate_limit import RateLimiter
from app.database import Base, get_db
from app.main import app

# Skip the dev-only create_all in the app lifespan (it targets Postgres).
settings.environment = "test"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Limiters key on client IP; every TestClient shares one, so clear between tests.
    RateLimiter.reset_all()
    # No context manager -> lifespan events don't fire (we don't want them here).
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def auth_headers(client: TestClient, email: str, password: str = "password123", **kw) -> dict:
    """Register (idempotently) + log in, returning an Authorization header."""
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": email.split("@")[0], **kw},
    )
    res = client.post("/auth/login", data={"username": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
