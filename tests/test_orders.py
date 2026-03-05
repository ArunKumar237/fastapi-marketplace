import pytest

from tests.factories import (
    create_test_address,
    create_test_category,
    create_test_product,
    create_test_store,
    create_test_user,
)

pytestmark = pytest.mark.asyncio


async def _setup_order_context(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")
    customer = await create_test_user(client, role="customer")

    category = await create_test_category(client, admin["headers"], name="Order Category")
    await create_test_store(client, vendor["headers"], name="Order Store")
    product = await create_test_product(
        client,
        vendor["headers"],
        category_id=category["id"],
        name="Order Product",
        price="100.00",
        stock=10,
    )
    address = await create_test_address(client, customer["headers"])

    return {
        "admin": admin,
        "vendor": vendor,
        "customer": customer,
        "product": product,
        "address": address,
    }


async def test_order_placement_success_stock_decrement_snapshot_and_cart_clear(client):
    ctx = await _setup_order_context(client)

    add_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": ctx["product"]["id"], "quantity": 2},
        headers=ctx["customer"]["headers"],
    )
    assert add_resp.status_code == 200

    place_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": ctx["address"]["id"]},
        headers=ctx["customer"]["headers"],
    )
    assert place_resp.status_code == 201
    order = place_resp.json()
    assert order["total_amount"] == "200.00"
    assert order["items"][0]["unit_price"] == "100.00"

    product_resp = await client.get(f"/api/v1/products/{ctx['product']['id']}")
    assert product_resp.status_code == 200
    assert product_resp.json()["stock"] == 8

    cart_resp = await client.get("/api/v1/cart", headers=ctx["customer"]["headers"])
    assert cart_resp.status_code == 200
    assert cart_resp.json()["items"] == []

    update_price = await client.put(
        f"/api/v1/products/{ctx['product']['id']}",
        json={"price": "175.00"},
        headers=ctx["vendor"]["headers"],
    )
    assert update_price.status_code == 200

    detail_resp = await client.get(
        f"/api/v1/me/orders/{order['id']}",
        headers=ctx["customer"]["headers"],
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["items"][0]["unit_price"] == "100.00"


async def test_order_placement_fails_for_empty_cart(client):
    ctx = await _setup_order_context(client)

    place_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": ctx["address"]["id"]},
        headers=ctx["customer"]["headers"],
    )
    assert place_resp.status_code == 400
    assert place_resp.json()["error"] == "EMPTY_CART"


async def test_order_placement_fails_for_insufficient_stock_after_cart_add(client):
    ctx = await _setup_order_context(client)

    add_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": ctx["product"]["id"], "quantity": 2},
        headers=ctx["customer"]["headers"],
    )
    assert add_resp.status_code == 200

    reduce_stock = await client.put(
        f"/api/v1/products/{ctx['product']['id']}",
        json={"stock": 1},
        headers=ctx["vendor"]["headers"],
    )
    assert reduce_stock.status_code == 200

    place_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": ctx["address"]["id"]},
        headers=ctx["customer"]["headers"],
    )
    assert place_resp.status_code == 400
    assert place_resp.json()["error"] == "INSUFFICIENT_STOCK"


async def test_order_placement_fails_for_invalid_shipping_address(client):
    ctx = await _setup_order_context(client)
    other_customer = await create_test_user(client, role="customer")
    other_address = await create_test_address(client, other_customer["headers"])

    add_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": ctx["product"]["id"], "quantity": 1},
        headers=ctx["customer"]["headers"],
    )
    assert add_resp.status_code == 200

    place_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": other_address["id"]},
        headers=ctx["customer"]["headers"],
    )
    assert place_resp.status_code == 400
    assert place_resp.json()["error"] == "INVALID_SHIPPING_ADDRESS"


async def test_order_status_transition_rules(client):
    ctx = await _setup_order_context(client)

    add_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": ctx["product"]["id"], "quantity": 1},
        headers=ctx["customer"]["headers"],
    )
    assert add_resp.status_code == 200

    place_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": ctx["address"]["id"]},
        headers=ctx["customer"]["headers"],
    )
    assert place_resp.status_code == 201
    order = place_resp.json()

    vendor_orders = await client.get(
        "/api/v1/vendor/orders?page=1&size=20",
        headers=ctx["vendor"]["headers"],
    )
    assert vendor_orders.status_code == 200
    order_item_id = vendor_orders.json()["items"][0]["order_item_id"]

    invalid_transition = await client.patch(
        f"/api/v1/vendor/orders/{order_item_id}/status",
        json={"status": "delivered"},
        headers=ctx["vendor"]["headers"],
    )
    assert invalid_transition.status_code == 400
    assert invalid_transition.json()["error"] == "INVALID_STATUS_TRANSITION"

    confirmed = await client.patch(
        f"/api/v1/vendor/orders/{order_item_id}/status",
        json={"status": "confirmed"},
        headers=ctx["vendor"]["headers"],
    )
    assert confirmed.status_code == 200

    shipped = await client.patch(
        f"/api/v1/vendor/orders/{order_item_id}/status",
        json={"status": "shipped"},
        headers=ctx["vendor"]["headers"],
    )
    assert shipped.status_code == 200

    delivered = await client.patch(
        f"/api/v1/vendor/orders/{order_item_id}/status",
        json={"status": "delivered"},
        headers=ctx["vendor"]["headers"],
    )
    assert delivered.status_code == 200

    order_detail = await client.get(
        f"/api/v1/me/orders/{order['id']}",
        headers=ctx["customer"]["headers"],
    )
    assert order_detail.status_code == 200
    assert order_detail.json()["status"] == "delivered"
