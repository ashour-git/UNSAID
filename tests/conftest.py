import os
import tempfile
from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path

_temp_static = tempfile.mkdtemp()
_temp_img = tempfile.mkdtemp()
_temp_templates = tempfile.mkdtemp()

from app.core.config import settings

settings.static_dir = Path(_temp_static)
settings.campaign_img_dir = Path(_temp_img)
settings.templates_dir = Path(_temp_templates)
settings.enable_rate_limit = False

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import sign_session_value
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.csrf import CSRFMiddleware

TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

_original_dispatch = CSRFMiddleware.dispatch


async def _patched_dispatch(self, request, call_next):
    response = await call_next(request)
    return response


CSRFMiddleware.dispatch = _patched_dispatch

import app.db.session as db_session_mod
import app.main as main_module

db_session_mod.engine = test_engine
db_session_mod.AsyncSessionLocal = TestSessionLocal
main_module.engine = test_engine
main_module.AsyncSessionLocal = TestSessionLocal


def _write_template(relative_path: str, content: str) -> None:
    full_path = Path(_temp_templates) / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


_write_template(
    "error.html",
    """<!DOCTYPE html>
<html>
<head><title>{{ status_code }} — UNSAID</title>
<style>body{font-family:serif;background:#0a0a0a;color:#e0e0e0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}.error-page{text-align:center}.error-code{font-size:6rem;font-weight:200;letter-spacing:0.1em;margin:0}.error-detail{font-size:1.1rem;opacity:0.6}</style>
</head>
<body>
<div class="error-page">
<h1 class="error-code">{{ status_code }}</h1>
<p class="error-detail">{{ detail }}</p>
</div>
</body>
</html>""",
)

_write_template(
    "index.html",
    "{% for product in products %}<div>{{ product.name }}</div>{% endfor %}",
)

_write_template(
    "product_detail.html",
    "<h1>{{ product.name }}</h1><p>{{ product.description }}</p>",
)

_write_template(
    "legal_page.html",
    "<h1>{{ title }}</h1>{% for section in sections %}<h2>{{ section.heading }}</h2>{% endfor %}",
)

_write_template(
    "contact_page.html",
    "<h1>Contact</h1>",
)

_write_template(
    "account/signup.html",
    "{% if error %}<p class=\"error\">{{ error }}</p>{% endif %}<form></form>",
)

_write_template(
    "account/login.html",
    "{% if error %}<p class=\"error\">{{ error }}</p>{% endif %}<form></form>",
)

_write_template(
    "account/dashboard.html",
    "<h1>Account</h1>{% for order in orders %}<div>{{ order.order_number }}</div>{% endfor %}",
)

_write_template(
    "account/orders.html",
    "<h1>My Orders</h1>{% for order in orders %}<div>{{ order.order_number }}</div>{% endfor %}",
)

_write_template(
    "account/order_detail.html",
    "<h1>Order {{ order.order_number }}</h1>",
)

_write_template(
    "admin/login.html",
    "{% if error %}<p class=\"error\">{{ error }}</p>{% endif %}<form></form>",
)

_write_template(
    "admin/dashboard.html",
    "<h1>Admin Dashboard</h1>",
)

_write_template(
    "admin/orders.html",
    "<h1>Orders</h1>{% for order in orders %}<div>{{ order.order_number }} - {{ order.status }}</div>{% endfor %}",
)

_write_template(
    "admin/order_detail.html",
    "<h1>Order {{ order.order_number }}</h1>",
)

_write_template(
    "admin/products.html",
    "<h1>Products</h1>",
)

_write_template(
    "admin/insights.html",
    "<h1>Insights</h1>",
)

_write_template(
    "partials/order_dispatch.html",
    "<p>{{ whatsapp_url }}</p>",
)

_write_template(
    "partials/newsletter_response.html",
    "<p>{{ email }}</p>",
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_session):
    from app.models.user import CustomerProfile, User
    from app.core.security import hash_password

    user = User(
        email="customer@example.com",
        password_hash=hash_password("StrongP@ss1"),
        role="customer",
        is_active=True,
    )
    test_session.add(user)
    await test_session.flush()
    profile = CustomerProfile(
        user_id=user.id,
        full_name="Test Customer",
        phone="+1234567890",
        city="Test City",
        shipping_address="123 Test St",
    )
    test_session.add(profile)
    await test_session.commit()
    return user


@pytest_asyncio.fixture
async def test_admin_user(test_session):
    from app.models.user import User
    from app.core.security import hash_password

    user = User(
        email="admin@example.com",
        password_hash=hash_password("AdminP@ss1"),
        role="admin",
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    return user


@pytest_asyncio.fixture
async def test_product(test_session):
    from app.models.product import Product

    product = Product(
        name="Test Fragrance",
        subtitle="Test subtitle",
        concentration="Extrait de Parfum",
        volume="30ml",
        description="A test fragrance description.",
        olfactory_notes={"top": ["Bergamot"], "heart": ["Rose"], "base": ["Musk"]},
        price=Decimal("199.00"),
        stock=10,
        image_url="/static/images/test.svg",
        dynamic_slug="test-fragrance",
    )
    test_session.add(product)
    await test_session.commit()
    return product


@pytest_asyncio.fixture
async def test_order(test_session, test_product, test_user):
    from app.services.orders import create_order

    order = await create_order(
        test_session,
        product=test_product,
        customer_name="Test Customer",
        customer_phone="+1234567890",
        shipping_address="123 Test St",
        city="Test City",
        whatsapp_url="https://wa.me/1234567890?text=test",
        user=test_user,
    )
    await test_session.commit()
    return order


@pytest_asyncio.fixture
def auth_headers(test_user):
    from app.models.user import User

    cookie_value = sign_session_value(test_user.id)
    return {"Cookie": f"unsaid_session={cookie_value}"}


@pytest_asyncio.fixture
def admin_auth_headers(test_admin_user):
    cookie_value = sign_session_value(test_admin_user.id)
    return {"Cookie": f"unsaid_session={cookie_value}"}