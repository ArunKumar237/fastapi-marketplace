from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.config import get_settings
from tests.factories import create_test_user

pytestmark = pytest.mark.asyncio


async def test_register_login_and_protected_endpoint(client):
    user_ctx = await create_test_user(client, role="customer")

    me_resp = await client.get("/api/v1/auth/me", headers=user_ctx["headers"])
    assert me_resp.status_code == 200
    payload = me_resp.json()
    assert payload["email"] == user_ctx["email"]
    assert payload["role"] == "customer"


async def test_duplicate_email_registration_rejected(client):
    email = "duplicate@example.com"
    payload = {
        "email": email,
        "password": "Passw0rd123",
        "full_name": "First User",
        "role": "customer",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/auth/register",
        json={**payload, "full_name": "Second User"},
    )
    assert second.status_code == 400


async def test_invalid_credentials_rejected(client):
    user_ctx = await create_test_user(client, role="customer")

    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": user_ctx["email"], "password": "WrongPassword123"},
    )
    assert bad_login.status_code == 401


async def test_refresh_token_returns_new_access_token(client):
    user_ctx = await create_test_user(client, role="customer")

    refresh = await client.post(
        f"/api/v1/auth/refresh?refresh_token={user_ctx['refresh_token']}"
    )
    assert refresh.status_code == 200
    body = refresh.json()
    assert body["access_token"]
    assert body["refresh_token"] == user_ctx["refresh_token"]


async def test_expired_token_rejected(client):
    user_ctx = await create_test_user(client, role="customer")
    settings = get_settings()

    expired_payload = {
        "sub": user_ctx["user"]["id"],
        "role": "customer",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "INVALID_TOKEN"


async def test_missing_auth_header_rejected(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_role_enforcement_customer_cannot_access_admin_category_create(client):
    customer = await create_test_user(client, role="customer")

    resp = await client.post(
        "/api/v1/categories",
        json={"name": "Admin Only Category", "description": "nope", "is_active": True},
        headers=customer["headers"],
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"] == "INSUFFICIENT_PERMISSIONS"
