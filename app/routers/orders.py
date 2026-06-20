from decimal import Decimal
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.templates import templates
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.services.analytics import record_event
from app.services.auth import get_current_user
from app.services.orders import create_order
from app.utils.forms import parse_form


router = APIRouter(prefix="/api/orders", tags=["Orders"])


def require_field(form: dict[str, str], field_name: str) -> str:
    value = form.get(field_name, "").strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Missing required order field: {field_name}",
        )

    return value


def normalize_whatsapp_number(phone_number: str) -> str:
    return "".join(character for character in phone_number if character.isdigit())


def validate_phone(phone_number: str) -> str:
    digits = "".join(c for c in phone_number if c.isdigit())
    if len(digits) < 7:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Phone number must contain at least 7 digits",
        )
    return phone_number


def format_price(price: Decimal) -> str:
    return f"{price:.2f}"


def build_order_message(
    *,
    product: Product,
    customer_name: str,
    customer_phone: str,
    shipping_address: str,
    city: str,
) -> str:
    return "\n".join(
        [
            "UNSAID ORDER REQUEST",
            "--------------------",
            f"Product: {product.name}",
            f"SKU: {product.dynamic_slug}",
            f"Concentration: {product.concentration}",
            f"Volume: {product.volume}",
            f"Price: {format_price(product.price)}",
            "",
            "CUSTOMER DETAILS",
            f"Name: {customer_name}",
            f"Phone: {customer_phone}",
            f"Shipping Address: {shipping_address}",
            f"City: {city}",
            "",
            "Please confirm availability, delivery timing, and payment steps.",
        ]
    )


def build_whatsapp_url(message: str) -> str:
    phone_number = normalize_whatsapp_number(settings.whatsapp_business_number)
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WhatsApp business number is not configured",
        )

    return f"https://wa.me/{phone_number}?text={quote(message)}"


@router.post("/whatsapp", response_class=HTMLResponse)
async def dispatch_whatsapp_order(
    request: Request,
    current_user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    form = await parse_form(request)
    product_slug = require_field(form, "product_slug")
    customer_name = require_field(form, "customer_name")
    customer_phone = validate_phone(require_field(form, "customer_phone"))
    customer_email = form.get("customer_email", "").strip() or None
    shipping_address = require_field(form, "shipping_address")
    city = require_field(form, "city")
    source = form.get("source", "site") or "site"

    result = await session.execute(
        select(Product).where(Product.dynamic_slug == product_slug)
    )
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected fragrance not found",
        )

    message = build_order_message(
        product=product,
        customer_name=customer_name,
        customer_phone=customer_phone,
        shipping_address=shipping_address,
        city=city,
    )
    whatsapp_url = build_whatsapp_url(message)
    order = await create_order(
        session,
        product=product,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        shipping_address=shipping_address,
        city=city,
        whatsapp_url=whatsapp_url,
        user=current_user,
        source=source,
    )
    await record_event(
        session,
        "order_submitted",
        user=current_user,
        product_id=product.id,
        order_id=order.id,
        metadata={"source": source, "city": city},
    )
    await session.commit()

    return templates.TemplateResponse(
        request=request,
        name="partials/order_dispatch.html",
        context={"order": order, "product": product, "whatsapp_url": whatsapp_url},
    )
