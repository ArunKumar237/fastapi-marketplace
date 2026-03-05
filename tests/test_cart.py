import pytest

from tests.factories import (
    create_test_category,
    create_test_product,
    create_test_store,
    create_test_user,
)

pytestmark = pytest.mark.asyncio


async def test_cart_add_update_remove_flow(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")
    customer = await create_test_user(client, role="customer")

    category = await create_test_category(client, admin["headers"])
    await create_test_store(client, vendor["headers"])
    product = await create_test_product(
        client,
        vendor["headers"],
        category_id=category["id"],
        price="20.00",
        stock=10,
    )

    add_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": product["id"], "quantity": 2},
        headers=customer["headers"],
    )
    assert add_resp.status_code == 200

    cart_resp = await client.get("/api/v1/cart", headers=customer["headers"])
    assert cart_resp.status_code == 200
    cart = cart_resp.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["items"][0]["line_subtotal"] == "40.00"

    update_resp = await client.put(
        f"/api/v1/cart/items/{product['id']}",
        json={"quantity": 3},
        headers=customer["headers"],
    )
    assert update_resp.status_code == 200

    updated_cart = await client.get("/api/v1/cart", headers=customer["headers"])
    assert updated_cart.status_code == 200
    assert updated_cart.json()["items"][0]["quantity"] == 3

    remove_resp = await client.delete(
        f"/api/v1/cart/items/{product['id']}",
        headers=customer["headers"],
    )
    assert remove_resp.status_code == 204

    final_cart = await client.get("/api/v1/cart", headers=customer["headers"])
    assert final_cart.status_code == 200
    assert final_cart.json()["items"] == []


async def test_cart_rejects_quantity_above_stock(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")
    customer = await create_test_user(client, role="customer")

    category = await create_test_category(client, admin["headers"])
    await create_test_store(client, vendor["headers"])
    product = await create_test_product(
        client,
        vendor["headers"],
        category_id=category["id"],
        stock=2,
    )

    resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": product["id"], "quantity": 3},
        headers=customer["headers"],
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "INSUFFICIENT_STOCK"


async def test_cart_update_to_zero_removes_item(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")
    customer = await create_test_user(client, role="customer")

    category = await create_test_category(client, admin["headers"])
    await create_test_store(client, vendor["headers"])
    product = await create_test_product(
        client,
        vendor["headers"],
        category_id=category["id"],
        stock=5,
    )

    add_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": product["id"], "quantity": 1},
        headers=customer["headers"],
    )
    assert add_resp.status_code == 200

    update_resp = await client.put(
        f"/api/v1/cart/items/{product['id']}",
        json={"quantity": 0},
        headers=customer["headers"],
    )
    assert update_resp.status_code == 200

    cart_resp = await client.get("/api/v1/cart", headers=customer["headers"])
    assert cart_resp.status_code == 200
    assert cart_resp.json()["items"] == []
