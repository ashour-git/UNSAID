from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, OrderStatusEvent
from app.models.product import Product
from app.models.user import User


ORDER_STATUSES = {
    "new",
    "contacted",
    "confirmed",
    "packed",
    "shipped",
    "delivered",
    "cancelled",
}


async def next_order_number(session: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    count = await session.scalar(select(func.count(Order.id))) or 0
    return f"UNS-{year}-{count + 1:06d}"


async def create_order(
    session: AsyncSession,
    *,
    product: Product,
    customer_name: str,
    customer_phone: str,
    shipping_address: str,
    city: str,
    whatsapp_url: str,
    user: User | None = None,
    customer_email: str | None = None,
    source: str = "site",
) -> Order:
    order = Order(
        order_number=await next_order_number(session),
        user_id=user.id if user else None,
        customer_name=customer_name,
        customer_email=customer_email or (user.email if user else None),
        customer_phone=customer_phone,
        shipping_address=shipping_address,
        city=city,
        status="new",
        source=source,
        subtotal=Decimal(product.price),
        currency="USD",
        whatsapp_url=whatsapp_url,
    )
    session.add(order)
    await session.flush()
    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name_snapshot=product.name,
            product_slug_snapshot=product.dynamic_slug,
            unit_price_snapshot=Decimal(product.price),
            quantity=1,
            line_total=Decimal(product.price),
        )
    )
    session.add(
        OrderStatusEvent(
            order_id=order.id,
            from_status=None,
            to_status="new",
            actor_user_id=user.id if user else None,
            note="Order enquiry created from storefront.",
        )
    )
    return order


async def update_order_status(
    session: AsyncSession,
    *,
    order: Order,
    status: str,
    actor: User,
    note: str = "",
) -> Order:
    if status not in ORDER_STATUSES:
        raise ValueError("Invalid order status")
    previous_status = order.status
    order.status = status
    now = datetime.now(timezone.utc)
    if status == "confirmed" and order.confirmed_at is None:
        order.confirmed_at = now
    if status == "delivered" and order.delivered_at is None:
        order.delivered_at = now
    if status == "cancelled" and order.cancelled_at is None:
        order.cancelled_at = now
    session.add(
        OrderStatusEvent(
            order_id=order.id,
            from_status=previous_status,
            to_status=status,
            actor_user_id=actor.id,
            note=note,
        )
    )
    return order
