import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_db
from app.models.user import User
from app.services.analytics import record_event, subscribe_email
from app.services.auth import get_current_user
from app.utils.forms import parse_form

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.post("/events")
async def create_analytics_event(
    request: Request,
    current_user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    form = await parse_form(request)
    event_name = form.get("event_name", "").strip()
    if not event_name:
        return {"status": "ignored"}
    product_id = int(form["product_id"]) if form.get("product_id", "").isdigit() else None
    await record_event(
        session,
        event_name,
        anonymous_id=form.get("anonymous_id", ""),
        user=current_user,
        product_id=product_id,
        metadata={"source": form.get("source", "site")},
    )
    await session.commit()
    return {"status": "recorded"}


@router.post("/newsletter", response_class=HTMLResponse)
async def newsletter_signup(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    form = await parse_form(request)
    email = form.get("email", "")
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await subscribe_email(session, email=email, source=form.get("source", "footer"))
        await record_event(session, "newsletter_signup", metadata={"source": "footer"})
        await session.commit()
    return templates.TemplateResponse(
        request=request,
        name="partials/newsletter_response.html",
        context={"email": email},
    )
