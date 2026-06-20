import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.session import get_db, AsyncSessionLocal, engine, init_db


@pytest.mark.asyncio
async def test_order_submission_with_valid_data(async_client, test_product):
    response = await async_client.post(
        "/api/orders/whatsapp",
        data={
            "product_slug": "test-fragrance",
            "customer_name": "Test Customer",
            "customer_phone": "+1234567890",
            "customer_email": "test@example.com",
            "shipping_address": "123 Test St",
            "city": "Test City",
            "source": "site",
        },
    )
    assert response.status_code == 200
    assert "wa.me" in response.text


@pytest.mark.asyncio
async def test_order_submission_persists_order_in_database(
    async_client, test_session, test_product
):
    count_before = await test_session.scalar(
        __import__("sqlalchemy").select(
            __import__("sqlalchemy").func.count(__import__("app.models.order", fromlist=["Order"]).Order.id)
        )
    )

    response = await async_client.post(
        "/api/orders/whatsapp",
        data={
            "product_slug": "test-fragrance",
            "customer_name": "Test Customer",
            "customer_phone": "+1234567890",
            "shipping_address": "123 Test St",
            "city": "Test City",
        },
    )
    assert response.status_code == 200

    count_after = await test_session.scalar(
        __import__("sqlalchemy").select(
            __import__("sqlalchemy").func.count(__import__("app.models.order", fromlist=["Order"]).Order.id)
        )
    )
    assert count_after == (count_before or 0) + 1


@pytest.mark.asyncio
async def test_order_submission_returns_whatsapp_url(async_client, test_product):
    response = await async_client.post(
        "/api/orders/whatsapp",
        data={
            "product_slug": "test-fragrance",
            "customer_name": "Test Customer",
            "customer_phone": "+1234567890",
            "shipping_address": "123 Test St",
            "city": "Test City",
        },
    )
    assert response.status_code == 200
    assert "https://wa.me/" in response.text


@pytest.mark.asyncio
async def test_order_submission_with_missing_fields(async_client):
    response = await async_client.post(
        "/api/orders/whatsapp",
        data={
            "product_slug": "test-fragrance",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_customer_order_history_shows_their_orders(
    async_client, test_order, auth_headers
):
    response = await async_client.get(
        "/account/orders", headers=auth_headers
    )
    assert response.status_code == 200
    assert test_order.order_number in response.text


@pytest.mark.asyncio
async def test_admin_can_view_all_orders(
    async_client, test_order, admin_auth_headers
):
    response = await async_client.get(
        "/admin/orders", headers=admin_auth_headers
    )
    assert response.status_code == 200
    assert test_order.order_number in response.text


@pytest.mark.asyncio
async def test_admin_can_update_order_status(
    async_client, test_session, test_order, test_admin_user, admin_auth_headers
):
    response = await async_client.post(
        f"/admin/orders/{test_order.id}/status",
        data={
            "status": "confirmed",
            "note": "Test status update",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 303

    await test_session.refresh(test_order)
    assert test_order.status == "confirmed"


@pytest.mark.asyncio
async def test_order_status_event_is_created_on_status_change(
    async_client, test_session, test_order, test_admin_user, admin_auth_headers
):
    from sqlalchemy import select, func
    from app.models.order import OrderStatusEvent

    count_before = await test_session.scalar(
        select(func.count(OrderStatusEvent.id)).where(
            OrderStatusEvent.order_id == test_order.id
        )
    )

    await async_client.post(
        f"/admin/orders/{test_order.id}/status",
        data={
            "status": "shipped",
            "note": "Test status event",
        },
        headers=admin_auth_headers,
    )

    count_after = await test_session.scalar(
        select(func.count(OrderStatusEvent.id)).where(
            OrderStatusEvent.order_id == test_order.id
        )
    )
    assert count_after == (count_before or 0) + 1