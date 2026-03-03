"""Shared pytest fixtures for the NDIS CRM backend test suite."""

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import get_current_user, require_role
from app.db import Base, get_db

# ---------------------------------------------------------------------------
# In-memory SQLite async engine (no Postgres needed in CI)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once per test session."""
    # Import all models so that Base.metadata is fully populated before create_all.
    import app.models.audit_log  # noqa: F401
    import app.models.budget_alert  # noqa: F401
    import app.models.document  # noqa: F401
    import app.models.email_thread  # noqa: F401
    import app.models.invoice  # noqa: F401
    import app.models.invoice_line_item  # noqa: F401
    import app.models.participant  # noqa: F401
    import app.models.provider  # noqa: F401
    import app.models.statement  # noqa: F401
    import app.models.support_category  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.xero_connection  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated async DB session per test with rollback."""
    async with TestSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Mock auth helpers – bypass Auth0 in tests
# ---------------------------------------------------------------------------

_MOCK_ADMIN = {
    "sub": "test|admin",
    "roles": ["Admin", "Coordinator"],
    "https://ndis-crm.com/roles": ["Admin", "Coordinator"],
}


# ---------------------------------------------------------------------------
# HTTP test client fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_client(db_session):
    """AsyncClient wired to the FastAPI app with the test DB injected."""
    from main import app

    # Override DB dependency
    async def override_get_db():
        yield db_session

    # Override auth dependencies so no token is needed
    async def override_current_user():
        return _MOCK_ADMIN

    def override_require_role(role: str):
        async def _dep():
            return _MOCK_ADMIN

        return _dep

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[require_role] = override_require_role

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_PLAN_PAYLOAD = {
    "plan_start_date": "2024-07-01",
    "plan_end_date": "2025-06-30",
    "total_funding": "50000.00",
    "plan_manager": "Self-managed",
}


def make_participant_payload(ndis_number: str | None = None) -> dict:
    """Return a participant payload with a unique NDIS number."""
    return {
        "ndis_number": ndis_number or f"NDIS{uuid.uuid4().hex[:8].upper()}",
        "first_name": "Alice",
        "last_name": "Smith",
        "date_of_birth": "1990-06-15",
        "email": "alice@example.com",
        "phone": "0400000001",
        "address": "1 Test Street, Sydney NSW 2000",
    }


@pytest_asyncio.fixture
async def sample_participant(test_client):
    """Create and return a sample participant via the API (unique per test)."""
    payload = make_participant_payload()
    resp = await test_client.post("/api/v1/participants/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
