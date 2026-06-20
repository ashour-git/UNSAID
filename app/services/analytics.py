from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent, NewsletterSubscriber
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User


async def record_event(
    session: AsyncSession,
    event_name: str,
    *,
    anonymous_id: str = "",
    user: User | None = None,
    product_id: int | None = None,
    order_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> AnalyticsEvent:
    event = AnalyticsEvent(
        event_name=event_name,
        anonymous_id=anonymous_id,
        user_id=user.id if user else None,
        product_id=product_id,
        order_id=order_id,
        metadata_json=metadata or {},
    )
    session.add(event)
    return event


async def subscribe_email(
    session: AsyncSession,
    *,
    email: str,
    source: str = "footer",
) -> NewsletterSubscriber:
    normalized = email.strip().lower()
    result = await session.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == normalized)
    )
    subscriber = result.scalar_one_or_none()
    if subscriber is None:
        subscriber = NewsletterSubscriber(email=normalized, source=source, is_active=True)
        session.add(subscriber)
    else:
        subscriber.is_active = True
        subscriber.source = source
    return subscriber


async def build_business_metrics(session: AsyncSession, days: int = 30) -> dict[str, Any]:
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=days)

    orders_result = await session.execute(
        select(Order).where(Order.created_at >= period_start).order_by(Order.created_at.desc())
    )
    orders = list(orders_result.scalars().all())

    events_result = await session.execute(
        select(AnalyticsEvent).where(AnalyticsEvent.created_at >= period_start)
    )
    events = list(events_result.scalars().all())

    items_result = await session.execute(
        select(OrderItem, Product.name)
        .join(Product, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.created_at >= period_start)
    )
    item_rows = list(items_result.all())

    stock_result = await session.execute(select(Product).order_by(Product.stock, Product.id))
    products = list(stock_result.scalars().all())

    revenue = sum((order.subtotal for order in orders), Decimal("0"))
    status_counts = Counter(order.status for order in orders)
    event_counts = Counter(event.event_name for event in events)
    product_counts: Counter[str] = Counter()
    for item, product_name in item_rows:
        product_counts[product_name] += item.quantity

    top_products = [
        {"name": name, "orders": count}
        for name, count in product_counts.most_common(5)
    ]
    low_stock = [
        {"name": product.name, "stock": product.stock}
        for product in products
        if product.stock <= 8
    ][:5]

    checkout_starts = event_counts.get("checkout_opened", 0)
    order_submissions = len(orders)
    conversion_rate = (order_submissions / checkout_starts * 100) if checkout_starts else 0

    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "orders_total": len(orders),
        "new_orders": status_counts.get("new", 0),
        "confirmed_orders": status_counts.get("confirmed", 0),
        "delivered_orders": status_counts.get("delivered", 0),
        "cancelled_orders": status_counts.get("cancelled", 0),
        "revenue_estimate": float(revenue),
        "checkout_starts": checkout_starts,
        "order_submissions": order_submissions,
        "conversion_rate": round(conversion_rate, 1),
        "chat_messages": event_counts.get("chat_message", 0),
        "quiz_completions": event_counts.get("quiz_completed", 0),
        "product_views": event_counts.get("product_view", 0),
        "newsletter_signups": await session.scalar(select(func.count(NewsletterSubscriber.id))) or 0,
        "status_counts": dict(status_counts),
        "event_counts": dict(event_counts),
        "top_products": top_products,
        "low_stock": low_stock,
    }
