import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

_DEF_PASSWORD = "Passw0rd123"
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _load_base_database_url() -> str:
    env_file = Path(__file__).resolve().parents[1] / ".env"
    values = dotenv_values(env_file)
    file_url = values.get("DATABASE_URL")
    if file_url:
        return file_url

    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    raise RuntimeError("DATABASE_URL is required to run tests")


_BASE_DATABASE_URL = _load_base_database_url()
_BASE_URL = make_url(_BASE_DATABASE_URL)
_TEST_DB_NAME = f"{_BASE_URL.database}_test"
_TEST_DATABASE_URL = _BASE_URL.set(database=_TEST_DB_NAME).render_as_string(
    hide_password=False
)

# Force app to use dedicated test database.
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
os.environ.setdefault("DEBUG", "False")

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.database import (  # noqa: E402
    AsyncSessionLocal,
    Base,
    ensure_database_schema,
    get_db,
)
from app.main import app  # noqa: E402


async def _ensure_test_database_exists() -> None:
    conn = await asyncpg.connect(
        user=_BASE_URL.username,
        password=_BASE_URL.password,
        host=_BASE_URL.host or "localhost",
        port=_BASE_URL.port or 5432,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{_TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    await _ensure_test_database_exists()
    await ensure_database_schema()
    yield


@pytest_asyncio.fixture(autouse=True)
async def clean_database(setup_test_database: None) -> AsyncGenerator[None, None]:
    table_names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    if table_names:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
            )
            await session.commit()

    yield


@pytest.fixture(autouse=True)
def disable_async_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.order.send_order_confirmation.delay", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        "app.services.order.send_status_update.delay", lambda *args, **kwargs: None
    )


@pytest_asyncio.fixture(scope="session")
async def client(setup_test_database: None) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db() -> AsyncGenerator:
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_user_and_login(client: AsyncClient):
    async def _create(role: str = "customer", **overrides):
        import uuid

        email = overrides.pop("email", f"{role}.{uuid.uuid4().hex[:10]}@example.com")
        password = overrides.pop("password", _DEF_PASSWORD)
        payload = {
            "email": email,
            "password": password,
            "full_name": overrides.pop("full_name", f"{role.title()} User"),
            "role": role,
            "phone": overrides.pop("phone", None),
        }
        payload.update(overrides)

        register_resp = await client.post("/api/v1/auth/register", json=payload)
        assert register_resp.status_code == 201, register_resp.text

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        tokens = login_resp.json()

        return {
            "user": register_resp.json(),
            "email": email,
            "password": password,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
        }

    return _create
