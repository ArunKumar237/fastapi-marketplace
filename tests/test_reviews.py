import pytest

from tests.factories import (
    create_test_address,
    create_test_category,
    create_test_product,
    create_test_store,
    create_test_user,
)

pytestmark = pytest.mark.asyncio


async def test_create_and_list_reviews(client):
    admin = await create_test_user(client, role="admin")
    vendor = await create_test_user(client, role="vendor")
    customer = await create_test_user(client, role="customer")

    category = await create_test_category(client, admin["headers"], name="Reviews Cat")
    await create_test_store(client, vendor["headers"], name="Review Store")
    product = await create_test_product(
        client,
        vendor["headers"],
        category_id=category["id"],
        name="Review Product",
        price="199.99",
        stock=5,
    )
    address = await create_test_address(client, customer["headers"])

    add_cart_resp = await client.post(
        "/api/v1/cart/items",
        json={"product_id": product["id"], "quantity": 1},
        headers=customer["headers"],
    )
    assert add_cart_resp.status_code == 200, add_cart_resp.text

    order_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": address["id"]},
        headers=customer["headers"],
    )
    assert order_resp.status_code == 201, order_resp.text
    vendor_orders_resp = await client.get(
        "/api/v1/vendor/orders", headers=vendor["headers"]
    )
    assert vendor_orders_resp.status_code == 200, vendor_orders_resp.text
    order_item_id = vendor_orders_resp.json()["items"][0]["order_item_id"]

    for next_status in ("confirmed", "shipped", "delivered"):
        update_resp = await client.patch(
            f"/api/v1/vendor/orders/{order_item_id}/status",
            json={"status": next_status},
            headers=vendor["headers"],
        )
        assert update_resp.status_code == 200, update_resp.text

    create_resp = await client.post(
        f"/api/v1/products/{product['id']}/reviews",
        json={
            "rating": 5,
            "comment": "Great product",
        },
        headers=customer["headers"],
    )
    assert create_resp.status_code == 201, create_resp.text

    list_resp = await client.get(f"/api/v1/products/{product['id']}/reviews")
    assert list_resp.status_code == 200, list_resp.text
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["rating"] == 5
