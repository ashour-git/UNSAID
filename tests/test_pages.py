import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.session import get_db, AsyncSessionLocal, engine, init_db


@pytest.mark.asyncio
async def test_homepage_returns_200(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_product_detail_page_returns_200(async_client, test_product):
    response = await async_client.get(
        f"/products/{test_product.dynamic_slug}"
    )
    assert response.status_code == 200
    assert test_product.name in response.text


@pytest.mark.asyncio
async def test_404_page_returns_styled_html(async_client):
    response = await async_client.get(
        "/nonexistent-page", headers={"Accept": "text/html"}
    )
    assert response.status_code == 404
    assert "text/html" in response.headers.get("content-type", "")
    assert "error-page" in response.text.lower() or "error" in response.text.lower()


@pytest.mark.asyncio
async def test_robots_txt_returns_valid_content(async_client):
    response = await async_client.get("/robots.txt")
    assert response.status_code == 200
    content = response.text
    assert "User-agent" in content
    assert "Disallow" in content
    assert "Sitemap" in content


@pytest.mark.asyncio
async def test_sitemap_xml_returns_valid_xml(async_client, test_product):
    response = await async_client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "application/xml" in response.headers.get("content-type", "")
    assert "<?xml" in response.text
    assert "<urlset" in response.text
    assert test_product.dynamic_slug in response.text


@pytest.mark.asyncio
async def test_privacy_page_returns_200(async_client):
    response = await async_client.get("/privacy")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_terms_page_returns_200(async_client):
    response = await async_client.get("/terms")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_shipping_page_returns_200(async_client):
    response = await async_client.get("/shipping")
    assert response.status_code == 200