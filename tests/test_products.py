import pytest

from tests.factories import (
    create_test_category,
    create_test_product,
    create_test_store,
    create_test_user,
)

pytestmark = pytest.mark.asyncio


async def test_vendor_product_crud_and_soft_delete(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")

    category = await create_test_category(client, admin["headers"], name="Electronics")
    await create_test_store(client, vendor["headers"], name="Vendor Product Store")

    product = await create_test_product(
        client,
        vendor["headers"],
        category_id=category["id"],
        name="Phone",
        price="120.00",
        stock=5,
    )

    update_resp = await client.put(
        f"/api/v1/products/{product['id']}",
        json={"price": "150.00", "stock": 6},
        headers=vendor["headers"],
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["price"] == "150.00"
    assert update_resp.json()["stock"] == 6

    delete_resp = await client.delete(
        f"/api/v1/products/{product['id']}",
        headers=vendor["headers"],
    )
    assert delete_resp.status_code == 204

    public_get = await client.get(f"/api/v1/products/{product['id']}")
    assert public_get.status_code == 404


async def test_vendor_cannot_update_other_vendor_product(client):
    admin = await create_test_user(client, role="admin")
    vendor_a = await create_test_user(client, role="vendor")
    vendor_b = await create_test_user(client, role="vendor")

    category = await create_test_category(client, admin["headers"], name="Books")
    await create_test_store(client, vendor_a["headers"], name="A Store")
    await create_test_store(client, vendor_b["headers"], name="B Store")

    product = await create_test_product(
        client,
        vendor_a["headers"],
        category_id=category["id"],
        name="Vendor A Product",
    )

    resp = await client.put(
        f"/api/v1/products/{product['id']}",
        json={"name": "Vendor B Edit"},
        headers=vendor_b["headers"],
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "PRODUCT_OWNERSHIP_REQUIRED"


async def test_products_pagination_filter_and_search(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")

    category_a = await create_test_category(client, admin["headers"], name="Phones")
    category_b = await create_test_category(client, admin["headers"], name="Laptops")
    store = await create_test_store(client, vendor["headers"], name="Catalog Store")

    await create_test_product(
        client,
        vendor["headers"],
        category_id=category_a["id"],
        name="Alpha Phone",
        price="100.00",
    )
    await create_test_product(
        client,
        vendor["headers"],
        category_id=category_a["id"],
        name="Beta Phone",
        price="200.00",
    )
    await create_test_product(
        client,
        vendor["headers"],
        category_id=category_b["id"],
        name="Gamma Laptop",
        price="500.00",
    )

    page_resp = await client.get("/api/v1/products?page=1&size=1")
    assert page_resp.status_code == 200
    page_body = page_resp.json()
    assert page_body["total"] == 3
    assert len(page_body["items"]) == 1

    filter_resp = await client.get(f"/api/v1/products?category_id={category_a['id']}")
    assert filter_resp.status_code == 200
    assert filter_resp.json()["total"] == 2

    search_resp = await client.get("/api/v1/products?search=phone")
    assert search_resp.status_code == 200
    search_body = search_resp.json()
    assert search_body["total"] == 2
    assert all("phone" in item["name"].lower() for item in search_body["items"])

    store_filter = await client.get(f"/api/v1/products?store_id={store['id']}")
    assert store_filter.status_code == 200
    assert store_filter.json()["total"] == 3


async def test_create_product_invalid_price_rejected(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")

    category = await create_test_category(client, admin["headers"])
    await create_test_store(client, vendor["headers"])

    resp = await client.post(
        "/api/v1/products",
        json={
            "name": "Invalid Price Product",
            "description": "bad",
            "price": "-1.00",
            "stock": 5,
            "category_id": category["id"],
        },
        headers=vendor["headers"],
    )
    assert resp.status_code == 422
