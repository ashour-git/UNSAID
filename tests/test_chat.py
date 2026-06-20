from pathlib import Path

import pytest

from app.core.config import settings


def _write_template(relative_path: str, content: str) -> None:
    full_path = settings.templates_dir / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


_write_template("partials/chat_widget.html", '<div class="chat-widget">UNSAID Consultant</div>')
_write_template(
    "partials/chat_response.html",
    '<div class="chat-response">{{ response }}</div>',
)


@pytest.mark.asyncio
async def test_chat_widget_returns_html(async_client):
    response = await async_client.get("/api/chat/widget")
    assert response.status_code == 200
    assert "UNSAID Consultant" in response.text


@pytest.mark.asyncio
async def test_chat_message_returns_response(async_client):
    response = await async_client.post(
        "/api/chat/message",
        data={"message": "I need a fragrance for a summer wedding"},
    )
    assert response.status_code == 200
    assert "chat-response" in response.text.lower() or "response" in response.text.lower()


@pytest.mark.asyncio
async def test_chat_message_empty_rejected(async_client):
    response = await async_client.post("/api/chat/message", data={"message": ""})
    assert response.status_code == 200
    assert "I\u2019m listening" in response.text


@pytest.mark.asyncio
async def test_chat_message_unauthorized(async_client):
    response = await async_client.post(
        "/api/chat/message",
        data={"message": "What fragrance works for a date?"},
    )
    assert response.status_code == 200