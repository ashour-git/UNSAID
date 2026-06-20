import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.session import get_db, AsyncSessionLocal, engine, init_db


@pytest.mark.asyncio
async def test_analytics_event_creation(async_client, test_session):
    from sqlalchemy import select
    from app.models.analytics import AnalyticsEvent

    count_before = await test_session.scalar(
        __import__("sqlalchemy").select(
            __import__("sqlalchemy").func.count(AnalyticsEvent.id)
        )
    )

    response = await async_client.post(
        "/api/analytics/events",
        data={
            "event_name": "product_view",
            "anonymous_id": "test-anon-123",
            "product_id": "1",
            "source": "site",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "recorded"

    count_after = await test_session.scalar(
        __import__("sqlalchemy").select(
            __import__("sqlalchemy").func.count(AnalyticsEvent.id)
        )
    )
    assert count_after == (count_before or 0) + 1


@pytest.mark.asyncio
async def test_newsletter_signup(async_client, test_session):
    from sqlalchemy import select
    from app.models.analytics import NewsletterSubscriber

    response = await async_client.post(
        "/api/analytics/newsletter",
        data={
            "email": "subscriber@example.com",
            "source": "footer",
        },
    )
    assert response.status_code == 200
    assert "subscriber@example.com" in response.text

    result = await test_session.execute(
        select(NewsletterSubscriber).where(
            NewsletterSubscriber.email == "subscriber@example.com"
        )
    )
    subscriber = result.scalar_one_or_none()
    assert subscriber is not None
    assert subscriber.email == "subscriber@example.com"
    assert subscriber.source == "footer"
    assert subscriber.is_active is True


@pytest.mark.asyncio
async def test_metrics_aggregation(test_session, test_order, test_product):
    from app.services.analytics import build_business_metrics

    metrics = await build_business_metrics(test_session, days=30)
    assert "orders_total" in metrics
    assert "revenue_estimate" in metrics
    assert "status_counts" in metrics
    assert "event_counts" in metrics
    assert "top_products" in metrics
    assert "low_stock" in metrics
    assert "conversion_rate" in metrics
    assert isinstance(metrics["orders_total"], int)
    assert isinstance(metrics["revenue_estimate"], float)