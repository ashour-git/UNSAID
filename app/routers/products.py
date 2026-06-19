from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.product import Product
from app.schemas.product import ProductListResponse, ProductRead


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=ProductListResponse)
async def list_fragrances(
    session: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    result = await session.execute(select(Product).order_by(Product.id))
    products = list(result.scalars().all())

    return ProductListResponse(items=products, count=len(products))


@router.get("/{dynamic_slug}", response_model=ProductRead)
async def get_fragrance_by_slug(
    dynamic_slug: str,
    session: AsyncSession = Depends(get_db),
) -> Product:
    result = await session.execute(
        select(Product).where(Product.dynamic_slug == dynamic_slug)
    )
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found",
        )

    return product
