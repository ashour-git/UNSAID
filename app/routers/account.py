from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import sign_session_value
from app.core.templates import templates
from app.db.session import get_db
from app.models.order import Order
from app.models.user import CustomerProfile, User
from app.services.auth import authenticate_user, create_user, get_user_by_email, require_user
from app.services.brute_force import failed_login_tracker
from app.services.password import is_common_password, validate_password_strength
from app.utils.forms import parse_form

router = APIRouter(prefix="/account", tags=["Account"])


def set_session_cookie(response: RedirectResponse, user: User) -> RedirectResponse:
    response.set_cookie(
        settings.session_cookie_name,
        sign_session_value(user.id),
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=60 * 60 * 24 * 30,
    )
    return response


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="account/signup.html", context={"error": ""})


@router.post("/signup")
async def signup(request: Request, session: AsyncSession = Depends(get_db)) -> Response:
    form = await parse_form(request)
    email = form.get("email", "").lower()
    password = form.get("password", "")

    if not email or not password:
        return templates.TemplateResponse(
            request=request,
            name="account/signup.html",
            context={"error": "Email and password are required."},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    valid, reason = validate_password_strength(password)
    if not valid:
        return templates.TemplateResponse(
            request=request,
            name="account/signup.html",
            context={"error": reason},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    if is_common_password(password):
        return templates.TemplateResponse(
            request=request,
            name="account/signup.html",
            context={"error": "That password is too common. Choose a stronger one."},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    if await get_user_by_email(session, email):
        return templates.TemplateResponse(
            request=request,
            name="account/signup.html",
            context={"error": "An account with this email already exists."},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    user = await create_user(
        session,
        email=email,
        password=password,
        full_name=form.get("full_name", ""),
        phone=form.get("phone", ""),
        city=form.get("city", ""),
        shipping_address=form.get("shipping_address", ""),
        marketing_opt_in=form.get("marketing_opt_in") == "on",
    )
    await session.commit()
    return set_session_cookie(RedirectResponse("/account", status_code=status.HTTP_303_SEE_OTHER), user)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="account/login.html", context={"error": ""})


@router.post("/login")
async def login(request: Request, session: AsyncSession = Depends(get_db)) -> Response:
    form = await parse_form(request)
    email = form.get("email", "").lower()
    ip = client_ip(request)

    if failed_login_tracker.is_locked_out(email, ip):
        return templates.TemplateResponse(
            request=request,
            name="account/login.html",
            context={"error": "Too many attempts. Please wait 30 minutes before trying again."},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    user = await authenticate_user(session, email=email, password=form.get("password", ""))
    if user is None:
        failed_login_tracker.record_failure(email, ip)
        return templates.TemplateResponse(
            request=request,
            name="account/login.html",
            context={"error": "Email or password is not correct."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    failed_login_tracker.reset(email, ip)
    destination = "/admin" if user.role == "admin" else "/account"
    return set_session_cookie(RedirectResponse(destination, status_code=status.HTTP_303_SEE_OTHER), user)


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name)
    return response


@router.get("", response_class=HTMLResponse)
async def account_home(
    request: Request,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    orders = await customer_orders(session, user)
    profile = await customer_profile(session, user)
    return templates.TemplateResponse(
        request=request,
        name="account/dashboard.html",
        context={"user": user, "profile": profile, "orders": orders},
    )


@router.get("/orders", response_class=HTMLResponse)
async def account_orders(
    request: Request,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    orders = await customer_orders(session, user)
    return templates.TemplateResponse(
        request=request,
        name="account/orders.html",
        context={"user": user, "orders": orders},
    )


@router.get("/orders/{order_number}", response_class=HTMLResponse)
async def account_order_detail(
    order_number: str,
    request: Request,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.status_events))
        .where(Order.order_number == order_number, Order.user_id == user.id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return templates.TemplateResponse(
        request=request,
        name="account/order_detail.html",
        context={"user": user, "order": order},
    )


async def customer_profile(session: AsyncSession, user: User) -> CustomerProfile | None:
    result = await session.execute(select(CustomerProfile).where(CustomerProfile.user_id == user.id))
    return result.scalar_one_or_none()


async def customer_orders(session: AsyncSession, user: User) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())