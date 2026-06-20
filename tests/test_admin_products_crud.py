from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.templates import templates
from app.models.product import Product, ProductOption


templates.env.loader.searchpath.append(str(Path(__file__).resolve().parents[1] / "app" / "templates"))


def product_form_data(**overrides):
    data = {
        "name": "UNSAID : Solace",
        "subtitle": "Stillness in bloom",
        "dynamic_slug": "unsaid-solace",
        "description": "A quiet floral fragrance with mineral edges.",
        "concentration": "Extrait de Parfum",
        "volume": "30ml",
        "price": "215.00",
        "compare_at_price": "250.00",
        "stock": "12",
        "image_url": "/static/images/solace.svg",
        "top_notes": "Bergamot, Neroli",
        "heart_notes": "Iris, Tea",
        "base_notes": "Musk, Cedar",
        "is_active": "on",
        "meta_title": "UNSAID : Solace",
        "meta_description": "A quiet floral fragrance.",
    }
    data.update(overrides)
    return data


async def load_product(test_session, product_id: int) -> Product | None:
    result = await test_session.execute(
        select(Product).where(Product.id == product_id).execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def load_option(test_session, option_id: int) -> ProductOption | None:
    result = await test_session.execute(
        select(ProductOption)
        .where(ProductOption.id == option_id)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_admin_product_new_page_requires_auth(async_client):
    response = await async_client.get("/admin/products/new", follow_redirects=False)

    assert response.status_code == 303


@pytest.mark.asyncio
async def test_admin_product_new_page_with_auth_returns_200(async_client, admin_auth_headers):
    response = await async_client.get("/admin/products/new", headers=admin_auth_headers)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_product_create_with_auth_redirects_and_persists(
    async_client, test_session, admin_auth_headers
):
    response = await async_client.post(
        "/admin/products",
        data=product_form_data(),
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/products"

    result = await test_session.execute(
        select(Product).where(Product.dynamic_slug == "unsaid-solace")
    )
    product = result.scalar_one_or_none()
    assert product is not None
    assert product.name == "UNSAID : Solace"
    assert product.subtitle == "Stillness in bloom"
    assert product.price == Decimal("215.00")
    assert product.compare_at_price == Decimal("250.00")
    assert product.stock == 12
    assert product.is_active is True
    assert product.olfactory_notes == {
        "top": ["Bergamot", "Neroli"],
        "heart": ["Iris", "Tea"],
        "base": ["Musk", "Cedar"],
    }


@pytest.mark.asyncio
async def test_admin_product_edit_page_with_auth_returns_200(
    async_client, test_product, admin_auth_headers
):
    response = await async_client.get(
        f"/admin/products/{test_product.id}/edit", headers=admin_auth_headers
    )

    assert response.status_code == 200
    assert test_product.name in response.text


@pytest.mark.asyncio
async def test_admin_product_update_with_auth_redirects_and_updates(
    async_client, test_session, test_product, admin_auth_headers
):
    response = await async_client.post(
        f"/admin/products/{test_product.id}",
        data=product_form_data(
            name="UNSAID : Nocturne",
            subtitle="After-dark restraint",
            dynamic_slug="unsaid-nocturne",
            description="A darker edit of the original formula.",
            price="275.00",
            compare_at_price="",
            stock="4",
            image_url="/static/images/nocturne.svg",
            top_notes="Black Pepper",
            heart_notes="Violet Leaf",
            base_notes="Incense, Amber",
            meta_title="UNSAID : Nocturne",
            meta_description="A darker edit.",
        ),
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/products"

    updated = await load_product(test_session, test_product.id)
    assert updated is not None
    assert updated.name == "UNSAID : Nocturne"
    assert updated.dynamic_slug == "unsaid-nocturne"
    assert updated.description == "A darker edit of the original formula."
    assert updated.price == Decimal("275.00")
    assert updated.compare_at_price is None
    assert updated.stock == 4
    assert updated.image_url == "/static/images/nocturne.svg"
    assert updated.meta_title == "UNSAID : Nocturne"
    assert updated.olfactory_notes == {
        "top": ["Black Pepper"],
        "heart": ["Violet Leaf"],
        "base": ["Incense", "Amber"],
    }


@pytest.mark.asyncio
async def test_admin_product_toggle_changes_is_active(
    async_client, test_session, test_product, admin_auth_headers
):
    original_is_active = test_product.is_active

    response = await async_client.post(
        f"/admin/products/{test_product.id}/toggle",
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/products"

    await test_session.refresh(test_product)
    assert test_product.is_active is (not original_is_active)


@pytest.mark.asyncio
async def test_admin_product_delete_removes_product(
    async_client, test_session, test_product, admin_auth_headers
):
    response = await async_client.post(
        f"/admin/products/{test_product.id}/delete",
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/products"
    assert await load_product(test_session, test_product.id) is None


@pytest.mark.asyncio
async def test_admin_product_add_option_persists_option(
    async_client, test_session, test_product, admin_auth_headers
):
    response = await async_client.post(
        f"/admin/products/{test_product.id}/options",
        data={"volume": "50ml", "price": "289.00", "stock": "7"},
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/admin/products/{test_product.id}/edit"

    result = await test_session.execute(
        select(ProductOption).where(ProductOption.product_id == test_product.id)
    )
    option = result.scalar_one_or_none()
    assert option is not None
    assert option.volume == "50ml"
    assert option.price == Decimal("289.00")
    assert option.stock == 7
    assert option.is_default is False


@pytest.mark.asyncio
async def test_admin_product_set_default_option_marks_one_default(
    async_client, test_session, test_product, admin_auth_headers
):
    first = ProductOption(
        product_id=test_product.id,
        volume="30ml",
        price=Decimal("199.00"),
        stock=5,
        is_default=True,
    )
    second = ProductOption(
        product_id=test_product.id,
        volume="50ml",
        price=Decimal("289.00"),
        stock=3,
        is_default=False,
    )
    test_session.add_all([first, second])
    await test_session.commit()

    response = await async_client.post(
        f"/admin/products/{test_product.id}/set-default-option",
        data={"option_id": str(second.id)},
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/admin/products/{test_product.id}/edit"

    await test_session.refresh(first)
    await test_session.refresh(second)
    assert first.is_default is False
    assert second.is_default is True


@pytest.mark.asyncio
async def test_admin_product_delete_option_removes_option(
    async_client, test_session, test_product, admin_auth_headers
):
    option = ProductOption(
        product_id=test_product.id,
        volume="50ml",
        price=Decimal("289.00"),
        stock=3,
        is_default=False,
    )
    test_session.add(option)
    await test_session.commit()

    response = await async_client.post(
        f"/admin/products/options/{option.id}/delete",
        headers=admin_auth_headers,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/admin/products/{test_product.id}/edit"
    assert await load_option(test_session, option.id) is None
