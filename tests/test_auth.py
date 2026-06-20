import pytest
from httpx import ASGITransport, AsyncClient

from app.core.csrf import generate_csrf_token
from app.main import app
from app.db.session import get_db, AsyncSessionLocal, engine, init_db


@pytest.mark.asyncio
async def test_customer_signup_with_valid_data(async_client, test_session):
    response = await async_client.post(
        "/account/signup",
        data={
            "email": "newuser@example.com",
            "password": "StrongP@ss1",
            "full_name": "New User",
            "phone": "+1234567890",
            "city": "Test City",
            "shipping_address": "123 Test St",
        },
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/account"


@pytest.mark.asyncio
async def test_signup_with_csrf_cookie_and_form_token_succeeds(async_client):
    csrf_token = generate_csrf_token()
    async_client.cookies.set("unsaid_csrf", csrf_token)

    response = await async_client.post(
        "/account/signup",
        data={
            "email": "csrf-signup@example.com",
            "password": "StrongP@ss1",
            "full_name": "CSRF Signup",
            "phone": "+1234567890",
            "city": "Test City",
            "shipping_address": "123 Test St",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/account"


@pytest.mark.asyncio
async def test_customer_signup_with_weak_password(async_client):
    response = await async_client.post(
        "/account/signup",
        data={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak User",
        },
    )
    assert response.status_code == 422
    assert "at least 8 characters" in response.text


@pytest.mark.asyncio
async def test_customer_signup_with_common_password(async_client):
    response = await async_client.post(
        "/account/signup",
        data={
            "email": "common@example.com",
            "password": "Password1",
            "full_name": "Common User",
        },
    )
    assert response.status_code == 422
    assert "too common" in response.text.lower()


@pytest.mark.asyncio
async def test_customer_signup_with_existing_email(async_client, test_user):
    response = await async_client.post(
        "/account/signup",
        data={
            "email": "customer@example.com",
            "password": "AnotherP@ss1",
            "full_name": "Duplicate User",
        },
    )
    assert response.status_code == 422
    assert "already exists" in response.text.lower()


@pytest.mark.asyncio
async def test_customer_login_with_valid_credentials(async_client, test_user):
    response = await async_client.post(
        "/account/login",
        data={
            "email": "customer@example.com",
            "password": "StrongP@ss1",
        },
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/account"
    assert "unsaid_session" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_customer_login_with_wrong_password(async_client, test_user):
    response = await async_client.post(
        "/account/login",
        data={
            "email": "customer@example.com",
            "password": "WrongP@ss1",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_login_with_non_existent_email(async_client):
    response = await async_client.post(
        "/account/login",
        data={
            "email": "noone@example.com",
            "password": "SomeP@ss1",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_with_valid_credentials(async_client, test_admin_user):
    response = await async_client.post(
        "/admin/login",
        data={
            "email": "admin@example.com",
            "password": "AdminP@ss1",
        },
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"


@pytest.mark.asyncio
async def test_admin_login_redirects_to_admin(async_client, test_admin_user):
    response = await async_client.post(
        "/account/login",
        data={
            "email": "admin@example.com",
            "password": "AdminP@ss1",
        },
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"


@pytest.mark.asyncio
async def test_logout_clears_session_cookie(async_client):
    response = await async_client.post("/account/logout")
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    set_cookie = response.headers.get("set-cookie", "")
    assert "unsaid_session=" in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower() or "unsaid_session=\"\"" in set_cookie


@pytest.mark.asyncio
async def test_unauthorized_access_to_admin_redirects_to_login(async_client):
    response = await async_client.get(
        "/admin", follow_redirects=False, headers={"Accept": "text/html"}
    )
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_unauthorized_access_to_account_redirects_to_login(async_client):
    response = await async_client.get(
        "/account", follow_redirects=False, headers={"Accept": "text/html"}
    )
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_customer_cannot_access_admin_routes(async_client, test_user, auth_headers):
    response = await async_client.get("/admin", headers=auth_headers, follow_redirects=False)
    assert response.status_code == 403
