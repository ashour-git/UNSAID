from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.media import campaign_image_for_index
from app.core.templates import templates
from app.db.session import get_db
from app.models.product import Product
from app.services.analytics import record_event
from app.utils.forms import parse_form


router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

ChoiceVector = dict[str, float]

ANSWER_VECTORS: dict[str, ChoiceVector] = {
    "self": {"self": 1.0, "gift": 0.0},
    "gift": {"self": 0.0, "gift": 1.0},
    "day": {"day": 1.0, "night": 0.0},
    "night": {"day": 0.0, "night": 1.0},
    "fresh": {"fresh": 1.0, "spicy": 0.0, "sweet": 0.0},
    "spicy": {"fresh": 0.0, "spicy": 1.0, "sweet": 0.0},
    "sweet": {"fresh": 0.0, "spicy": 0.0, "sweet": 1.0},
}

PRODUCT_VECTORS: dict[str, ChoiceVector] = {
    "unsaid-pulse": {
        "self": 0.85,
        "gift": 0.75,
        "day": 1.00,
        "night": 0.25,
        "fresh": 1.00,
        "spicy": 0.35,
        "sweet": 0.05,
    },
    "unsaid-chapter-i": {
        "self": 0.85,
        "gift": 0.85,
        "day": 0.45,
        "night": 0.95,
        "fresh": 0.25,
        "spicy": 1.00,
        "sweet": 0.20,
    },
    "unsaid-apex": {
        "self": 0.75,
        "gift": 0.95,
        "day": 0.35,
        "night": 0.85,
        "fresh": 0.20,
        "spicy": 0.90,
        "sweet": 0.15,
    },
    "unsaid-aura": {
        "self": 0.65,
        "gift": 0.80,
        "day": 0.75,
        "night": 0.35,
        "fresh": 0.55,
        "spicy": 0.05,
        "sweet": 0.75,
    },
    "unsaid-echo": {
        "self": 0.75,
        "gift": 0.45,
        "day": 0.15,
        "night": 1.00,
        "fresh": 0.05,
        "spicy": 0.65,
        "sweet": 0.25,
    },
    "unsaid-velvet": {
        "self": 0.55,
        "gift": 0.90,
        "day": 0.25,
        "night": 0.95,
        "fresh": 0.05,
        "spicy": 0.45,
        "sweet": 1.00,
    },
}


def build_user_vector(*answers: str) -> ChoiceVector:
    vector: ChoiceVector = {
        "self": 0.0,
        "gift": 0.0,
        "day": 0.0,
        "night": 0.0,
        "fresh": 0.0,
        "spicy": 0.0,
        "sweet": 0.0,
    }

    for answer in answers:
        for axis, value in ANSWER_VECTORS[answer].items():
            vector[axis] += value

    return vector


def score_product(user_vector: ChoiceVector, product_vector: ChoiceVector) -> float:
    return sum(
        user_vector[axis] * product_vector.get(axis, 0.0)
        for axis in user_vector
    )


def select_recommendation_slug(
    intent: str,
    atmosphere: str,
    imprint: str,
) -> str:
    user_vector = build_user_vector(intent, atmosphere, imprint)
    return max(
        PRODUCT_VECTORS,
        key=lambda slug: score_product(user_vector, PRODUCT_VECTORS[slug]),
    )


def validate_choice(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid quiz selection for {field_name}",
        )

    return value


@router.get("/start", response_class=HTMLResponse)
async def start_quiz(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="partials/quiz_step_1.html",
        context={},
    )


@router.post("/step/2", response_class=HTMLResponse)
async def quiz_step_two(request: Request) -> HTMLResponse:
    form = await parse_form(request)
    intent = validate_choice(form.get("intent", ""), {"self", "gift"}, "intent")

    return templates.TemplateResponse(
        request=request,
        name="partials/quiz_step_2.html",
        context={"intent": intent},
    )


@router.post("/step/3", response_class=HTMLResponse)
async def quiz_step_three(request: Request) -> HTMLResponse:
    form = await parse_form(request)
    intent = validate_choice(form.get("intent", ""), {"self", "gift"}, "intent")
    atmosphere = validate_choice(
        form.get("atmosphere", ""),
        {"day", "night"},
        "atmosphere",
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/quiz_step_3.html",
        context={"intent": intent, "atmosphere": atmosphere},
    )


@router.post("/evaluate", response_class=HTMLResponse)
async def evaluate_quiz(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    form = await parse_form(request)
    intent = validate_choice(form.get("intent", ""), {"self", "gift"}, "intent")
    atmosphere = validate_choice(
        form.get("atmosphere", ""),
        {"day", "night"},
        "atmosphere",
    )
    imprint = validate_choice(
        form.get("imprint", ""),
        {"fresh", "spicy", "sweet"},
        "imprint",
    )
    slug = select_recommendation_slug(intent, atmosphere, imprint)
    result = await session.execute(select(Product).where(Product.dynamic_slug == slug))
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommended fragrance not found",
        )

    context: dict[str, Any] = {
        "campaign_image": campaign_image_for_index(product.id - 1),
        "product": product,
        "intent": intent,
        "atmosphere": atmosphere,
        "imprint": imprint,
    }
    await record_event(
        session,
        "quiz_completed",
        product_id=product.id,
        metadata={"intent": intent, "atmosphere": atmosphere, "imprint": imprint},
    )
    await session.commit()
    return templates.TemplateResponse(
        request=request,
        name="partials/quiz_result.html",
        context=context,
    )
