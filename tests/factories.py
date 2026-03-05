import uuid
from typing import Any

from httpx import AsyncClient

DEFAULT_PASSWORD = "Passw0rd123"


def _uniq(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


async def create_test_user(
    client: AsyncClient,
    role: str = "customer",
    **overrides: Any,
) -> dict[str, Any]:
    email = overrides.pop("email", f"{role}.{uuid.uuid4().hex[:10]}@example.com")
    password = overrides.pop("password", DEFAULT_PASSWORD)
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


async def create_test_category(
    client: AsyncClient,
    admin_headers: dict[str, str],
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "name": overrides.pop("name", _uniq("category")),
        "description": overrides.pop("description", "Test category"),
        "is_active": overrides.pop("is_active", True),
    }
    payload.update(overrides)

    resp = await client.post("/api/v1/categories", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_test_store(
    client: AsyncClient,
    vendor_headers: dict[str, str],
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "name": overrides.pop("name", _uniq("store")),
        "description": overrides.pop("description", "Test store"),
        "product_count": overrides.pop("product_count", 0),
    }
    payload.update(overrides)

    resp = await client.post("/api/v1/stores", json=payload, headers=vendor_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_test_product(
    client: AsyncClient,
    vendor_headers: dict[str, str],
    category_id: str,
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "name": overrides.pop("name", _uniq("product")),
        "description": overrides.pop("description", "Test product"),
        "price": overrides.pop("price", "99.99"),
        "stock": overrides.pop("stock", 10),
        "category_id": overrides.pop("category_id", category_id),
    }
    payload.update(overrides)

    resp = await client.post("/api/v1/products", json=payload, headers=vendor_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_test_address(
    client: AsyncClient,
    customer_headers: dict[str, str],
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "label": overrides.pop("label", "Home"),
        "address_line_1": overrides.pop("address_line_1", "101 Main St"),
        "address_line_2": overrides.pop("address_line_2", None),
        "city": overrides.pop("city", "Austin"),
        "state": overrides.pop("state", "TX"),
        "postal_code": overrides.pop("postal_code", "78701"),
        "country": overrides.pop("country", "USA"),
        "is_default": overrides.pop("is_default", True),
    }
    payload.update(overrides)

    resp = await client.post(
        "/api/v1/me/addresses", json=payload, headers=customer_headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
