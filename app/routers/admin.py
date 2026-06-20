import json
import os
import re
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import sign_session_value
from app.core.templates import templates
from app.db.session import get_db
from app.models.order import Order
from app.models.product import Product, ProductOption
from app.models.user import User
from app.services.analytics import build_business_metrics
from app.services.auth import authenticate_user, require_admin
from app.services.insights import generate_insight_snapshot, latest_insight_snapshot
from app.services.orders import ORDER_STATUSES, update_order_status
from app.utils.forms import parse_form

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="admin/login.html", context={"error": ""})


@router.post("/login")
async def admin_login(request: Request, session: AsyncSession = Depends(get_db)) -> Response:
    form = await parse_form(request)
    user = await authenticate_user(session, email=form.get("email", ""), password=form.get("password", ""))
    if user is None or user.role != "admin":
        return templates.TemplateResponse(
            request=request,
            name="admin/login.html",
            context={"error": "Admin credentials are not correct."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    response = RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        settings.session_cookie_name,
        sign_session_value(user.id),
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=60 * 60 * 24 * 30,
    )
    return response


@router.post("/logout")
async def admin_logout() -> RedirectResponse:
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name)
    return response


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    metrics = await build_business_metrics(session)
    snapshot = await latest_insight_snapshot(session)
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={"metrics": metrics, "snapshot": snapshot},
    )


@router.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(
        select(Order).options(selectinload(Order.items), selectinload(Order.status_events)).order_by(Order.created_at.desc()).limit(100)
    )
    orders = list(result.scalars().all())
    return templates.TemplateResponse(
        request=request,
        name="admin/orders.html",
        context={"orders": orders, "statuses": sorted(ORDER_STATUSES)},
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    order_id: int,
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    order = await load_order(session, order_id)
    return templates.TemplateResponse(
        request=request,
        name="admin/order_detail.html",
        context={"order": order, "statuses": sorted(ORDER_STATUSES)},
    )


@router.post("/orders/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    form = await parse_form(request)
    order = await load_order(session, order_id)
    await update_order_status(
        session,
        order=order,
        status=form.get("status", "new"),
        actor=admin,
        note=form.get("note", ""),
    )
    await session.commit()
    return RedirectResponse(f"/admin/orders/{order.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(
        select(Product).options(selectinload(Product.options)).order_by(Product.id)
    )
    return templates.TemplateResponse(
        request=request,
        name="admin/products.html",
        context={"products": list(result.scalars().all())},
    )


@router.get("/insights", response_class=HTMLResponse)
async def admin_insights(
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    metrics = await build_business_metrics(session)
    snapshot = await latest_insight_snapshot(session)
    return templates.TemplateResponse(
        request=request,
        name="admin/insights.html",
        context={"metrics": metrics, "snapshot": snapshot},
    )


@router.post("/insights/generate")
async def admin_generate_insights(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    await generate_insight_snapshot(session)
    return RedirectResponse("/admin/insights", status_code=status.HTTP_303_SEE_OTHER)


async def load_order(session: AsyncSession, order_id: int) -> Order:
    result = await session.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.status_events))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def _generate_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')


async def _parse_product_form(request: Request) -> dict:
    form = await parse_form(request)
    raw_notes = form.get("olfactory_notes", "")
    try:
        olfactory_notes = json.loads(raw_notes)
    except (json.JSONDecodeError, TypeError):
        top = [n.strip() for n in form.get("top_notes", "").split(",") if n.strip()]
        heart = [n.strip() for n in form.get("heart_notes", "").split(",") if n.strip()]
        base = [n.strip() for n in form.get("base_notes", "").split(",") if n.strip()]
        olfactory_notes = {"top": top, "heart": heart, "base": base}
    return {
        "name": form.get("name", ""),
        "subtitle": form.get("subtitle", ""),
        "concentration": form.get("concentration", "Extrait de Parfum"),
        "volume": form.get("volume", "30ml"),
        "description": form.get("description", ""),
        "price": form.get("price", "0"),
        "compare_at_price": form.get("compare_at_price", ""),
        "stock": form.get("stock", "0"),
        "is_active": form.get("is_active", "on") == "on",
        "dynamic_slug": form.get("dynamic_slug", ""),
        "meta_title": form.get("meta_title", ""),
        "meta_description": form.get("meta_description", ""),
        "olfactory_notes": olfactory_notes,
        "image_url": form.get("image_url", ""),
    }


# ── Product CRUD ──────────────────────────────────────────────────────────────


@router.get("/products/new", response_class=HTMLResponse)
async def admin_product_new(
    request: Request,
    _: User = Depends(require_admin),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="admin/product_editor.html",
        context={"product": None},
    )


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def admin_product_edit(
    product_id: int,
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    result = await session.execute(
        select(Product).options(selectinload(Product.options)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return templates.TemplateResponse(
        request=request,
        name="admin/product_editor.html",
        context={"product": product},
    )


@router.post("/products")
async def admin_product_create(
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    data = await _parse_product_form(request)
    slug = data["dynamic_slug"] or _generate_slug(data["name"])
    compare_at_price = None
    if data["compare_at_price"]:
        compare_at_price = Decimal(data["compare_at_price"])
    product = Product(
        name=data["name"],
        subtitle=data["subtitle"],
        concentration=data["concentration"],
        volume=data["volume"],
        description=data["description"],
        price=Decimal(data["price"] or "0"),
        compare_at_price=compare_at_price,
        stock=int(data["stock"] or "0"),
        image_url=data["image_url"],
        dynamic_slug=slug,
        is_active=data["is_active"],
        meta_title=data["meta_title"],
        meta_description=data["meta_description"],
        olfactory_notes=data["olfactory_notes"],
    )
    session.add(product)
    await session.commit()
    return RedirectResponse("/admin/products", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/products/{product_id}")
async def admin_product_update(
    product_id: int,
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    data = await _parse_product_form(request)
    slug = data["dynamic_slug"] or _generate_slug(data["name"])
    compare_at_price = None
    if data["compare_at_price"]:
        compare_at_price = Decimal(data["compare_at_price"])
    product.name = data["name"]
    product.subtitle = data["subtitle"]
    product.concentration = data["concentration"]
    product.volume = data["volume"]
    product.description = data["description"]
    product.price = Decimal(data["price"] or "0")
    product.compare_at_price = compare_at_price
    product.stock = int(data["stock"] or "0")
    product.image_url = data["image_url"]
    product.dynamic_slug = slug
    product.is_active = data["is_active"]
    product.meta_title = data["meta_title"]
    product.meta_description = data["meta_description"]
    product.olfactory_notes = data["olfactory_notes"]
    await session.commit()
    return RedirectResponse("/admin/products", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/products/{product_id}/delete")
async def admin_product_delete(
    product_id: int,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return RedirectResponse("/admin/products", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/products/{product_id}/toggle")
async def admin_product_toggle(
    product_id: int,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.is_active = not product.is_active
    await session.commit()
    return RedirectResponse("/admin/products", status_code=status.HTTP_303_SEE_OTHER)


# ── Product Options ───────────────────────────────────────────────────────────


@router.post("/products/{product_id}/options")
async def admin_product_add_option(
    product_id: int,
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    form = await parse_form(request)
    option = ProductOption(
        product_id=product_id,
        volume=form.get("volume", "30ml"),
        price=Decimal(form.get("price", "0")),
        stock=int(form.get("stock", "0")),
        is_default=False,
    )
    session.add(option)
    await session.commit()
    return RedirectResponse(
        f"/admin/products/{product_id}/edit", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/products/options/{option_id}/delete")
async def admin_product_delete_option(
    option_id: int,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    result = await session.execute(select(ProductOption).where(ProductOption.id == option_id))
    option = result.scalar_one_or_none()
    if option is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found")
    product_id = option.product_id
    await session.delete(option)
    await session.commit()
    return RedirectResponse(
        f"/admin/products/{product_id}/edit", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/products/{product_id}/set-default-option")
async def admin_product_set_default_option(
    product_id: int,
    request: Request,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    form = await parse_form(request)
    option_id = int(form.get("option_id", "0"))
    result = await session.execute(
        select(ProductOption).where(ProductOption.product_id == product_id)
    )
    options = list(result.scalars().all())
    for opt in options:
        opt.is_default = opt.id == option_id
    await session.commit()
    return RedirectResponse(
        f"/admin/products/{product_id}/edit", status_code=status.HTTP_303_SEE_OTHER
    )


# ── Image Upload & Media ──────────────────────────────────────────────────────


UPLOADS_DIR = Path(__file__).resolve().parents[1] / "static" / "uploads" / "products"


@router.post("/upload")
async def admin_upload_image(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
) -> JSONResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = os.path.splitext(file.filename or ".png")[1] or ".png"
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    filepath = UPLOADS_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    return JSONResponse(content={"url": f"/static/uploads/products/{filename}"})


@router.get("/media", response_class=HTMLResponse)
async def admin_media_library(
    request: Request,
    _: User = Depends(require_admin),
) -> HTMLResponse:
    images: list[str] = []
    if UPLOADS_DIR.exists():
        images = sorted(
            [f"/static/uploads/products/{f.name}" for f in UPLOADS_DIR.iterdir() if f.is_file()],
            reverse=True,
        )
    return templates.TemplateResponse(
        request=request,
        name="admin/media.html",
        context={"images": images},
    )


@router.post("/media/delete")
async def admin_media_delete(
    request: Request,
    _: User = Depends(require_admin),
) -> RedirectResponse:
    form = await parse_form(request)
    filename = form.get("filename", "")
    if filename:
        filepath = UPLOADS_DIR / filename
        if filepath.exists():
            filepath.unlink()
    return RedirectResponse("/admin/media", status_code=status.HTTP_303_SEE_OTHER)
