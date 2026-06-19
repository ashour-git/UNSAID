from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.templates import templates
from app.db.session import get_db
from app.services.ai import chat_completion, fallback_consultation
from app.services.rag import build_rag_prompt, retrieve_context

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


async def parse_chat_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    form = parse_qs(body, keep_blank_values=True)
    return {key: values[-1].strip() for key, values in form.items() if values}


@router.post("/message", response_class=HTMLResponse)
async def chat_message(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    form = await parse_chat_form(request)
    user_message = form.get("message", "").strip()

    if not user_message:
        return templates.TemplateResponse(
            request=request,
            name="partials/chat_response.html",
            context={
                "response": "I’m listening. Tell me the occasion, the atmosphere, or the impression you want to leave.",
                "user_message": "",
            },
        )

    contexts = await retrieve_context(session, user_message)
    rag_prompt = build_rag_prompt(user_message, contexts)
    messages = [{"role": "user", "content": rag_prompt}]

    try:
        response_text = await chat_completion(messages)
    except Exception:
        response_text = fallback_consultation(user_message, contexts)

    return templates.TemplateResponse(
        request=request,
        name="partials/chat_response.html",
        context={"response": response_text, "user_message": user_message},
    )


@router.get("/widget", response_class=HTMLResponse)
async def chat_widget(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="partials/chat_widget.html",
        context={},
    )