import pytest


@pytest.mark.asyncio
async def test_products_api_returns_json(async_client, test_product):
    response = await async_client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["count"] >= 1
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_product_api_detail_returns_json(async_client, test_session):
    from decimal import Decimal
    from app.models.product import Product

    product = Product(
        name="UNSAID Apex",
        subtitle="Peak",
        concentration="Extrait de Parfum",
        volume="30ml",
        description="A bold and commanding fragrance.",
        olfactory_notes={"top": ["Bergamot"], "heart": ["Jasmine"], "base": ["Oud"]},
        price=Decimal("249.00"),
        stock=5,
        image_url="/static/images/apex.svg",
        dynamic_slug="unsaid-apex",
    )
    test_session.add(product)
    await test_session.commit()

    response = await async_client.get("/api/v1/products/unsaid-apex")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "UNSAID Apex"
    assert data["dynamic_slug"] == "unsaid-apex"


@pytest.mark.asyncio
async def test_product_api_not_found(async_client):
    response = await async_client.get("/api/v1/products/nonexistent")
    assert response.status_code == 404