from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.analytics import InsightSnapshot
from app.services.analytics import build_business_metrics
from app.services.ai import chat_completion


def deterministic_recommendations(metrics: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if metrics["new_orders"]:
        recommendations.append(f"Contact {metrics['new_orders']} new order enquiries before they cool down.")
    if metrics["conversion_rate"] < 35 and metrics["checkout_starts"]:
        recommendations.append("Review checkout friction; conversion from drawer open to order is below target.")
    if metrics["low_stock"]:
        first = metrics["low_stock"][0]
        recommendations.append(f"Check stock for {first['name']}; only {first['stock']} units remain.")
    if metrics["chat_messages"] > metrics["order_submissions"] * 2:
        recommendations.append("Use common consultation questions to strengthen product-page copy and reduce hesitation.")
    if not recommendations:
        recommendations.append("Keep monitoring product views, quiz completions, and order confirmations for a stronger trend signal.")
    return recommendations


def deterministic_summary(metrics: dict[str, Any]) -> str:
    top_product = metrics["top_products"][0]["name"] if metrics["top_products"] else "No clear product leader yet"
    return (
        f"In this period, UNSAID captured {metrics['orders_total']} order enquiries with "
        f"an estimated revenue of {metrics['revenue_estimate']:.2f}. "
        f"Checkout conversion is {metrics['conversion_rate']}% from {metrics['checkout_starts']} drawer opens. "
        f"Top demand signal: {top_product}."
    )


async def generate_insight_snapshot(session: AsyncSession, days: int = 30) -> InsightSnapshot:
    metrics = await build_business_metrics(session, days=days)
    summary = deterministic_summary(metrics)
    recommendations = deterministic_recommendations(metrics)
    model = "deterministic"

    if settings.groq_api_key:
        prompt = (
            "You are the UNSAID admin business analyst. Interpret these ecommerce metrics. "
            "Return a concise executive summary and 3 recommended actions. Ground every claim in the numbers. "
            f"Metrics: {metrics}"
        )
        try:
            ai_summary = await chat_completion([{"role": "user", "content": prompt}])
            if ai_summary:
                summary = ai_summary[:1200]
                model = settings.groq_model
        except Exception:
            model = "deterministic-fallback"

    snapshot = InsightSnapshot(
        period_start=datetime.fromisoformat(metrics["period_start"]),
        period_end=datetime.fromisoformat(metrics["period_end"]),
        metrics=metrics,
        summary=summary,
        recommendations=recommendations,
        model=model,
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)
    return snapshot


async def latest_insight_snapshot(session: AsyncSession) -> InsightSnapshot | None:
    result = await session.execute(
        select(InsightSnapshot).order_by(InsightSnapshot.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()
