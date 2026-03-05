import pytest

from tests.factories import create_test_user

pytestmark = pytest.mark.asyncio


async def test_vendor_can_create_and_update_own_store(client):
    vendor = await create_test_user(client, role="vendor")

    create_resp = await client.post(
        "/api/v1/stores",
        json={"name": "Vendor Store", "description": "My store", "product_count": 0},
        headers=vendor["headers"],
    )
    assert create_resp.status_code == 201
    store = create_resp.json()

    update_resp = await client.put(
        f"/api/v1/stores/{store['id']}",
        json={"description": "Updated description"},
        headers=vendor["headers"],
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated description"


async def test_customer_cannot_create_store(client):
    customer = await create_test_user(client, role="customer")

    resp = await client.post(
        "/api/v1/stores",
        json={"name": "Should Fail", "description": "No access", "product_count": 0},
        headers=customer["headers"],
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "INSUFFICIENT_PERMISSIONS"


async def test_vendor_cannot_update_other_vendor_store(client):
    vendor_a = await create_test_user(client, role="vendor")
    vendor_b = await create_test_user(client, role="vendor")

    create_resp = await client.post(
        "/api/v1/stores",
        json={"name": "Vendor A Store", "description": "Owned by A", "product_count": 0},
        headers=vendor_a["headers"],
    )
    assert create_resp.status_code == 201
    store_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/v1/stores/{store_id}",
        json={"description": "Hacked by B"},
        headers=vendor_b["headers"],
    )
    assert update_resp.status_code == 403
    assert update_resp.json()["error"] == "STORE_OWNERSHIP_REQUIRED"


async def test_admin_can_deactivate_store_and_public_get_returns_404(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")

    create_resp = await client.post(
        "/api/v1/stores",
        json={"name": "Store To Deactivate", "description": "temp", "product_count": 0},
        headers=vendor["headers"],
    )
    assert create_resp.status_code == 201
    store = create_resp.json()

    deactivate = await client.patch(
        f"/api/v1/stores/{store['id']}/status",
        json={"is_active": False},
        headers=admin["headers"],
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    public_get = await client.get(f"/api/v1/stores/{store['id']}")
    assert public_get.status_code == 404
