from decimal import Decimal
from urllib.parse import parse_qs, quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.templates import templates
from app.db.session import get_db
from app.models.product import Product


router = APIRouter(prefix="/api/orders", tags=["Orders"])


async def parse_order_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    form = parse_qs(body, keep_blank_values=True)
    return {key: values[-1].strip() for key, values in form.items() if values}


def require_field(form: dict[str, str], field_name: str) -> str:
    value = form.get(field_name, "").strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required order field: {field_name}",
        )

    return value


def normalize_whatsapp_number(phone_number: str) -> str:
    return "".join(character for character in phone_number if character.isdigit())


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
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    form = await parse_order_form(request)
    product_slug = require_field(form, "product_slug")
    customer_name = require_field(form, "customer_name")
    customer_phone = require_field(form, "customer_phone")
    shipping_address = require_field(form, "shipping_address")
    city = require_field(form, "city")

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

    return templates.TemplateResponse(
        request=request,
        name="partials/order_dispatch.html",
        context={"product": product, "whatsapp_url": whatsapp_url},
    )
