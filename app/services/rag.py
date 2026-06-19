import re
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeDocument

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z-]{2,}")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def score_document(query_tokens: Counter[str], document: KnowledgeDocument) -> float:
    content = f"{document.title} {document.category} {' '.join(document.tags)} {document.content}"
    document_tokens = Counter(tokenize(content))
    score = 0.0

    for token, query_count in query_tokens.items():
        score += min(query_count, document_tokens.get(token, 0)) * 3.0

    phrase = " ".join(query_tokens.keys())
    if phrase and phrase in content.lower():
        score += 6.0

    return score


async def retrieve_context(
    session: AsyncSession,
    query: str,
    top_k: int = 4,
) -> list[KnowledgeDocument]:
    result = await session.execute(select(KnowledgeDocument))
    documents = list(result.scalars().all())

    if not documents:
        return []

    query_tokens = Counter(tokenize(query))
    if not query_tokens:
        return documents[:top_k]

    ranked = sorted(
        documents,
        key=lambda document: score_document(query_tokens, document),
        reverse=True,
    )
    return ranked[:top_k]


def build_rag_prompt(
    user_message: str,
    contexts: list[KnowledgeDocument],
) -> str:
    if not contexts:
        context_text = "No database context was available. Use the UNSAID house knowledge from the system prompt."
    else:
        context_text = "\n\n".join(
            f"--- {document.title} ({document.category}) ---\n{document.content}"
            for document in contexts
        )

    return f"""Use the following UNSAID knowledge to answer the customer's question. Prioritise the documents over generic perfume advice.

FRAGRANCE KNOWLEDGE:
{context_text}

CUSTOMER QUESTION: {user_message}

YOUR RESPONSE:
- 2 to 4 sentences.
- Recommend one primary fragrance and optionally one alternative.
- Explain using notes, mood, occasion, and texture.
- Be elegant, direct, and useful."""


def contexts_to_plaintext(contexts: list[KnowledgeDocument]) -> str:
    return "\n".join(f"{document.title}: {document.content}" for document in contexts)
