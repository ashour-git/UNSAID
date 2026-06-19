from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.media import CAMPAIGN_IMAGES, campaign_image_for_index
from app.core.templates import templates
from app.db.session import get_db
from app.models.product import Product


router = APIRouter(tags=["Pages"])


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(select(Product).order_by(Product.id))
    products = list(result.scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "campaign_images": CAMPAIGN_IMAGES,
            "now": datetime.now(timezone.utc),
            "products": products,
        },
    )


@router.get("/products/{dynamic_slug}", response_class=HTMLResponse)
async def product_detail(
    dynamic_slug: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(
        select(Product).where(Product.dynamic_slug == dynamic_slug)
    )
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found",
        )

    related_result = await session.execute(
        select(Product).where(Product.dynamic_slug != dynamic_slug).order_by(Product.id).limit(3)
    )
    related_products = list(related_result.scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "campaign_image": campaign_image_for_index(product.id - 1),
            "now": datetime.now(timezone.utc),
            "product": product,
            "related_products": related_products,
        },
    )
