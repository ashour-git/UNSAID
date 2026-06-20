from pathlib import Path

import pytest

from app.core.config import settings


def _write_template(relative_path: str, content: str) -> None:
    full_path = settings.templates_dir / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


_write_template(
    "partials/quiz_step_1.html",
    '<div class="quiz-step-1"><h2>Step 1</h2></div>',
)
_write_template(
    "partials/quiz_step_2.html",
    '<div class="quiz-step-2"><h2>Step 2 — {{ intent }}</h2></div>',
)
_write_template(
    "partials/quiz_step_3.html",
    '<div class="quiz-step-3"><h2>Step 3 — {{ intent }} / {{ atmosphere }}</h2></div>',
)
_write_template(
    "partials/quiz_result.html",
    '<div class="quiz-result"><h2>{{ product.name }}</h2></div>',
)


@pytest.mark.asyncio
async def test_quiz_start_returns_html(async_client):
    response = await async_client.get("/api/quiz/start")
    assert response.status_code == 200
    assert "quiz-step-1" in response.text


@pytest.mark.asyncio
async def test_quiz_step2_returns_html(async_client):
    response = await async_client.post("/api/quiz/step/2", data={"intent": "self"})
    assert response.status_code == 200
    assert "quiz-step-2" in response.text


@pytest.mark.asyncio
async def test_quiz_step3_returns_html(async_client):
    response = await async_client.post(
        "/api/quiz/step/3", data={"intent": "self", "atmosphere": "day"}
    )
    assert response.status_code == 200
    assert "quiz-step-3" in response.text


@pytest.mark.asyncio
async def test_quiz_evaluate_returns_result(async_client, test_session):
    from decimal import Decimal
    from app.models.product import Product

    product = Product(
        name="UNSAID Pulse",
        subtitle="Clarity",
        concentration="Extrait de Parfum",
        volume="30ml",
        description="A fresh daytime fragrance.",
        olfactory_notes={"top": ["Bergamot"], "heart": ["Rose"], "base": ["Musk"]},
        price=Decimal("199.00"),
        stock=10,
        image_url="/static/images/pulse.svg",
        dynamic_slug="unsaid-pulse",
    )
    test_session.add(product)
    await test_session.commit()

    response = await async_client.post(
        "/api/quiz/evaluate",
        data={"intent": "self", "atmosphere": "day", "imprint": "fresh"},
    )
    assert response.status_code == 200
    assert "UNSAID Pulse" in response.text


@pytest.mark.asyncio
async def test_quiz_evaluate_invalid_imprint(async_client):
    response = await async_client.post(
        "/api/quiz/evaluate",
        data={"intent": "self", "atmosphere": "day", "imprint": "invalid"},
    )
    assert response.status_code == 422