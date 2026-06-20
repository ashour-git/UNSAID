from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, unsign_session_value, verify_password
from app.db.session import get_db
from app.models.user import CustomerProfile, User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    role: str = "customer",
    full_name: str = "",
    phone: str = "",
    city: str = "",
    shipping_address: str = "",
    marketing_opt_in: bool = False,
) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    if role == "customer":
        session.add(
            CustomerProfile(
                user_id=user.id,
                full_name=full_name or email.split("@", 1)[0],
                phone=phone,
                city=city,
                shipping_address=shipping_address,
                marketing_opt_in=marketing_opt_in,
            )
        )
    return user


async def authenticate_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    return user


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User | None:
    user_id = unsign_session_value(request.cookies.get(settings.session_cookie_name))
    if user_id is None:
        return None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


async def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/account/login"})
    return user


async def require_admin(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"})
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def seed_admin_user(session: AsyncSession) -> None:
    if not settings.admin_bootstrap_email or not settings.admin_bootstrap_password:
        return
    existing = await get_user_by_email(session, settings.admin_bootstrap_email)
    if existing is not None:
        return
    await create_user(
        session,
        email=settings.admin_bootstrap_email,
        password=settings.admin_bootstrap_password,
        role="admin",
    )
    await session.commit()
