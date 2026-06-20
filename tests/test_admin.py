import pytest


@pytest.mark.asyncio
async def test_admin_dashboard_requires_auth(async_client):
    response = await async_client.get("/admin", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_admin_dashboard_with_auth(async_client, admin_auth_headers):
    response = await async_client.get("/admin", headers=admin_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_orders_requires_auth(async_client):
    response = await async_client.get("/admin/orders", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_admin_orders_with_auth(async_client, admin_auth_headers):
    response = await async_client.get("/admin/orders", headers=admin_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_products_requires_auth(async_client):
    response = await async_client.get("/admin/products", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_admin_products_with_auth(async_client, admin_auth_headers):
    response = await async_client.get("/admin/products", headers=admin_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_insights_requires_auth(async_client):
    response = await async_client.get("/admin/insights", follow_redirects=False)
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_admin_insights_with_auth(async_client, admin_auth_headers):
    response = await async_client.get("/admin/insights", headers=admin_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_insights_generate(async_client, admin_auth_headers):
    response = await async_client.post(
        "/admin/insights/generate",
        headers=admin_auth_headers,
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/insights"